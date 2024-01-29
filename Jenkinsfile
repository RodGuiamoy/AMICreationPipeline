import java.util.UUID

class PrefixRegion {
    String prefix
    String region
}

class InstanceDetails {
    String instanceName
    String instanceId
    String region
}

// Function to find region by prefix
def findRegionByPrefix(String instanceName, List<PrefixRegion> prefixRegions) {
    for (pr in prefixRegions) {
        if (instanceName.startsWith(pr.prefix)) {
            return pr.region
        }
    }
    return null // Return null if no match is found
}

def setDelayedBuild(environment, region, instanceNames, ticketNumber, mode, scheduledBuildId, executionDateTime, delaySeconds) {
    // def job = Hudson.instance.getJob('AMICreationPipeline')
    def job = Jenkins.instance.getItemByFullName('AMICreationPipeline')

    if (job == null) {
        throw new IllegalStateException("Job not found: AMICreationPipeline")
    }

    def params = [
        new StringParameterValue('Environment', environment),
        new StringParameterValue('Region', region),
        new StringParameterValue('InstanceNames', instanceNames),
        new StringParameterValue('TicketNumber', ticketNumber),
        new StringParameterValue('Mode', mode),
        new StringParameterValue('ExecutionDateTime', executionDateTime),
        new StringParameterValue('ScheduledBuildId', scheduledBuildId)
    ]

    def future = job.scheduleBuild2(delaySeconds, new ParametersAction(params))
}

// Variables used in 'GetEnvironmentDetails' stage
def environment = ""
def account = ""
def role = ""

// Variables used in 'ValidateEC2' stage
def validInstances = []

// Variables used in 'ValidateSchedule' and 'ScheduleAMICreation' stages
String executionDateTimeStr = ""
int delaySeconds = 0

// Example array of PrefixRegion objects
def prefixRegions = [
    new PrefixRegion(prefix: "USEA", region: "us-east-1"),
    new PrefixRegion(prefix: "USWE", region: "us-west-1"),
    new PrefixRegion(prefix: "EUCE", region: "eu-central-1"),
    new PrefixRegion(prefix: "EUWE", region: "eu-west-1"),
    new PrefixRegion(prefix: "APAU", region: "ap-southeast-2"),
    new PrefixRegion(prefix: "APSP", region: "ap-southeast-1"),
    new PrefixRegion(prefix: "UOUE", region: "us-east-1"),
    new PrefixRegion(prefix: "UOUW", region: "us-west-1"),
    new PrefixRegion(prefix: "CACE", region: "ca-central-1")
]

pipeline {
    parameters {
        choice(
            name: 'Environment',
            choices: ['rod_aws','rod_aws_2'],
        )
        choice( 
            name: 'Region',
            choices: ['us-east-1','us-west-2','ap-southeast-1','ap-southeast-2','ca-central-1','eu-central-1','eu-west-1'],
        )
        string(
            name: 'InstanceNames',
            defaultValue: 'APSPTEST1,APSPTEST2,APSPTEST3,APAUTEST3,TEST', 
        )
        string(
            name: 'TicketNumber',
            defaultValue: 'SCTASK00000000',
        )
        choice( 
            name: 'Mode',
            choices: ['Adhoc','Scheduled'],
        )
        string(
            name: 'Date',
            defaultValue: 'MM/DD/YYYY',
        )
        string(
            name: 'Time',
            defaultValue: 'HH:MM',
        )
    }
    agent any

    stages {
        stage('GetEnvironmentDetails') {
            steps {
                script {
                    environment = params.Environment
                    
                    region = params.Region
                    role = 'AMICreationRole'
                    
                    switch (environment) {
                        case 'rod_aws':
                            account = '554249804926'
                            break
                        case 'rod_aws_2':
                            account = '992382788789'
                            break
                        default:
                            error("No matching environment details found that matches \"${environment}\". Exiting pipeline.")
                    }

                    echo "Successfully retrieved environment details for environment \"${environment}\""                   

                }
            }

        }
        stage('ValidateEC2') {
            steps {
                script {

                    // removes whitespaces from instance names and splits them
                    def instanceNames = params.InstanceNames.replaceAll("\\s+", "").split(',')
                    def invalidInstanceNames = []

                    // Populate valid and invalid instances arrays
                    instanceNames.each { instanceName ->
                        def region = findRegionByPrefix(instanceName, prefixRegions)
                        if (region) {
                            validInstances << new InstanceDetails(instanceName: instanceName, region: region)
                        } else {
                            invalidInstanceNames << instanceName
                        }
                    }

                    // Exit the pipeline if there are no valid instances
                    if (validInstances.isEmpty()) {
                        error("Unable to identify a region for all instances. Please verify that the correct account alias and EC2 instance names have been entered. Exiting the pipeline.")
                    }

                    if (invalidInstanceNames) {
                        unstable("Unable to identify a region for the following instances. Please verify that the correct account alias and EC2 instance names have been entered: ${invalidInstanceNames.join(', ')}")
                    }

                    // validInstances.each { println "${it.instance} - ${it.region}" }
                    def validInstanceRegionStr = validInstances.collect { it.instanceName + ": " + it.region }.join(', ')
                    echo "Successfully identified a region for the following instances: ${validInstanceRegionStr}"


                    
                    // Group instances by region
                    def instancesByRegion = validInstances.groupBy { it.region }

                    // Iterate over each region and verify instances
                    instancesByRegion.each { region, instances ->
                        def instanceNamesStr = instances.collect { it.instanceName }.join(', ')
                        // echo "Checking instances in region ${region}. Instance Names: ${instanceNamesStr}"

                        withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'rod_aws']]) {
                            withAWS(role: role, region: region, roleAccount: account, duration: '3600' ){
                                
                                // removes whitespaces from instance names
                                //def instanceNames = params.InstanceNames.replaceAll("\\s+", "")
                                
                                def awsCliCommand = "aws ec2 describe-instances --filters \"Name=tag:Name,Values=${instanceNamesStr}\" --region ${region} --output json"

                                // Executes the AWS CLI command and does some post-processing.
                                // The output includes the command at the top and can't be parsed so we have to drop the first line
                                def cliOutput = bat(script: awsCliCommand, returnStdout: true).trim()
                                cliOutput = cliOutput.readLines().drop(1).join("\n")

                                // Parse the CLI output as JSON
                                def jsonSlurper = new groovy.json.JsonSlurper()
                                def cliOutputJson = jsonSlurper.parseText(cliOutput)

                                // Check if 'Reservations' is empty
                                if (cliOutputJson.Reservations.isEmpty()) {
                                    // echo "No valid instances entered."
                                    unstable("None of the instances entered for region ${region} exists.")
                                    return
                                }

                                // Parse json output to get instance names and IDs
                                cliOutputJson.Reservations.each { reservation ->
                                    reservation.Instances.each { instance ->
                                        def instanceId = instance.InstanceId
                                        def instanceNameTag = instance.Tags.find { tag -> tag.Key == 'Name' }
                                        def instanceName = instanceNameTag ? instanceNameTag.Value : 'Unknown'                                      
                                        
                                        validInstances.find { it.instanceName == instanceName && it.region == region }?.instanceId = instanceId

                                    }
                                }

                                // Displays EC2s where their InstanceIDs are not identified hence does not exist
                                def nonExistentEc2s = validInstances.findAll { it.region == region && !it.instanceId }
                                if (!nonExistentEc2s.isEmpty()) {
                                    def nonExistentEc2Names = nonExistentEc2s.collect { it.instanceName }.join(', ')
                                    unstable("Non-existent EC2s for ${region}: ${nonExistentEc2Names}")
                                }
                            }
                        }
                    }

                    // Filter validInstances to get only objects with an instanceId
                    def validInstances = validInstances.findAll { it.instanceId }

                    // Displays a summary of valid EC2 instances
                    if (!validInstancesWithId.isEmpty()) {
                        def verifiedInstancesStr = "Verified instances:\n"
                        verifiedInstancesStr += "-----------------------\n"
                        validInstancesWithId.each { instance ->
                            verifiedInstancesStr += "Instance Name: ${instance.instanceName}\n"
                            verifiedInstancesStr += "Instance ID: ${instance.instanceId}\n"
                            verifiedInstancesStr += "Region: ${instance.region}\n"
                            verifiedInstancesStr += "-----------------------\n"
                        }

                        echo "${verifiedInstancesStr}"
                    }                    
                }
            }
        }
        // stage('ValidateSchedule') {
        //     when {
        //         expression { params.Mode == 'Scheduled'}
        //     }
        //     steps {
        //         script {

        //              // Specify the future date and time in military time (24-hour format)
        //             // String futureDateTime = "01/27/2024 14:25"
        //             executionDateTimeStr = params.Date + ' ' + params.Time

        //             Date executionDate = null

        //             try {
        //                 // Parse the future date and time
        //                 def dateFormat = new java.text.SimpleDateFormat("MM/dd/yyyy HH:mm")
        //                 executionDate = dateFormat.parse(executionDateTimeStr)
        //             }
        //             catch (ex) {
        //                 // Handle the error without failing the build
        //                 error("Unable to parse DateTime ${executionDateTimeStr}.")
        //             }
                    
        //             // Get the current date and time
        //             Date currentDate = new Date()

        //             // Calculate the difference in milliseconds
        //             long differenceInMillis = executionDate.time - currentDate.time

        //             // Convert the difference to seconds
        //             delaySeconds = differenceInMillis / 1000

        //             if (delaySeconds < 0) {
        //                 error ("Scheduled date must be in a future date.")
        //             }

        //             echo "Scheduled date ${executionDateTimeStr} is valid."
        //         }
        //     }
        // }
        // stage('ScheduleAMICreation') {
        //     when {
        //         expression { params.Mode == 'Scheduled'}
        //     }
        //     steps {
        //         script {
        //             echo "Will create scheduled Jenkins build."

        //             // We will set a unique valued parameter so manual triggered builds with the same parameters will not override the scheduled build
        //             def scheduledBuildId = UUID.randomUUID()
        //             scheduledBuildId = scheduledBuildId.toString()

        //             def validInstancesNameStr = validInstances.collect { it.name }.join(',')
                    
        //             // Example usage
        //             setDelayedBuild(environment, region, validInstancesNameStr, params.TicketNumber, 'Adhoc', scheduledBuildId, executionDateTimeStr, delaySeconds)
                    
        //         }
        //     }
        // }
        // stage('CreateAMI') {
        //     when {
        //         expression { params.Mode == 'Adhoc'}
        //     }
        //     steps {
        //         script {

        //             withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'rod_aws']]) {
        //                 withAWS(role: role, region: region, roleAccount: account, duration: '3600' ){

        //                     def ticketNumber = params.TicketNumber
                            
        //                     // validInstances = [
        //                     //     [id: 'TEST1', name: 'name1'],
        //                     //     [id: 'TEST', name: 'name2']
        //                     //     // Add more maps as needed
        //                     // ]

        //                     validInstances.each { instance ->
        //                         def instanceId = instance.id
        //                         def instanceName = instance.name

        //                         // Generate a three character, alphanumeric tag
        //                         def uuid = UUID.randomUUID()
        //                         def uuidString = uuid.toString()
        //                         def tag = uuidString[0..2]
                                
        //                         // Get UTC date
        //                         def utcDate = bat(script: 'powershell -command "[DateTime]::UtcNow.ToString(\'yyMMdd_HHmm\')"', returnStdout: true).trim()
        //                         utcDate = utcDate.readLines().drop(1).join("\n")

        //                         def amiName = "${ticketNumber}_${instanceName}_ADHOC_${utcDate}_${tag}"

        //                         echo "Creating AMI ${amiName} for ${instanceId}."

        //                         def awsCliCommand = "aws ec2 create-image --instance-id ${instanceId} --name ${amiName} --region ${region} --no-reboot --output json"

        //                         try {
        //                             // Executes the AWS CLI command and does some post-processing.
        //                             // The output includes the command at the top and can't be parsed so we have to drop the first line
        //                             def cliOutput = bat(script: awsCliCommand, returnStdout: true).trim()
        //                             cliOutput = cliOutput.readLines().drop(1).join("\n")
                                
        //                             // Parse the CLI output as JSON
        //                             def jsonSlurper = new groovy.json.JsonSlurper()
        //                             def cliOutputJson = jsonSlurper.parseText(cliOutput)

        //                             // Check if 'Reservations' is empty
        //                             if (cliOutputJson.ImageId.isEmpty()) {
        //                                 unstable("No AMI ID returned for ${instanceName}. Moving on to next EC2 instance.")
        //                                 return
        //                             }

        //                             echo "Successfully created AMI ${cliOutputJson.ImageId}."
                                    
        //                         } catch (ex) {
        //                             // Handle the error without failing the build
        //                             unstable('Error in creating AMI. Moving on to next EC2 instance.')
        //                         }
        //                     }
        //                 }
        //             }
        //         }
        //     }
        // }
    }
}




