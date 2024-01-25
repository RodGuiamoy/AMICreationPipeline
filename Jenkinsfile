import java.util.UUID
import hudson.model.*;

def environment = ""
def region = ""
def role = ""
def awsCredential = ""
def account = ""
def validInstances = []

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
            defaultValue: 'TEST1,TEST2,TEST3', 
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
                            awsCredential = 'rod_aws'
                            account = '554249804926'
                            break
                        case 'rod_aws_2':
                            awsCredential = 'rod_aws_2'
                            account = '992382788789'
                            break
                        default:
                            error("No matching environment details found that matches \"${environment}\". Exiting pipeline.")
                    }

                    echo "Successfully retrieved environment details for environment \"${environment}\""
                }
            }

        }
        // stage('ValidateEC2') {
        //     steps {
        //         script {
        //             withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'rod_aws']]) {
        //                 withAWS(role: role, region: region, roleAccount: account, duration: '3600' ){
                            
        //                     // removes whitespaces from instance names
        //                     def instanceNames = params.InstanceNames.replaceAll("\\s+", "")
                            
        //                     def awsCliCommand = "aws ec2 describe-instances --filters \"Name=tag:Name,Values=${instanceNames}\" --region ${region} --output json"

        //                     // Executes the AWS CLI command and does some post-processing.
        //                     // The output includes the command at the top and can't be parsed so we have to drop the first line
        //                     def cliOutput = bat(script: awsCliCommand, returnStdout: true).trim()
        //                     cliOutput = cliOutput.readLines().drop(1).join("\n")

        //                     // Parse the CLI output as JSON
        //                     def jsonSlurper = new groovy.json.JsonSlurper()
        //                     def cliOutputJson = jsonSlurper.parseText(cliOutput)

        //                     // Check if 'Reservations' is empty
        //                     if (cliOutputJson.Reservations.isEmpty()) {
        //                         // echo "No valid instances entered."
        //                         error("No valid instances entered. Exiting the pipeline.")
        //                     } 

        //                     // Parse json output to get instance names and IDs
        //                     cliOutputJson.Reservations.each { reservation ->
        //                         reservation.Instances.each { instance ->
        //                             def instanceId = instance.InstanceId
        //                             def instanceNameTag = instance.Tags.find { tag -> tag.Key == 'Name' }
        //                             def instanceName = instanceNameTag ? instanceNameTag.Value : 'Unknown'

        //                             validInstances << [id: instanceId, name: instanceName]

        //                         }
        //                     }

        //                     // Create a string representation of the validInstances array
        //                     def instanceStrings = validInstances.collect { it.name + ": " + it.id }.join(', ')
        //                     echo "Valid instances: ${instanceStrings}"

        //                     // Find and display invalid instance names
        //                     def instanceNamesSplit = instanceNames.split(',') 
        //                     def invalidInstanceNames = instanceNamesSplit.findAll { name -> !validInstances.find { it.name == name.trim() } }
        //                     if (invalidInstanceNames) {
        //                         unstable("Invalid instances: ${invalidInstanceNames.join(', ')}")
        //                     }
        //                 }
        //             }
        //         }
        //     }
        // }
        stage('ScheduleAMICreation') {
            when {
                expression { params.Mode == 'Scheduled'}
            }
            steps {
                script {
                    echo "Will create scheduled Jenkins build."

                    // We will set a unique valued parameter so manual triggered builds with the same parameters will not override the scheduled build
                    def hiddenParamUuid = UUID.randomUUID()
                    def hiddenParamUuidStr = hiddenParamUuid.toString()

                     // Specify the future date and time in military time (24-hour format)
                    String futureDateTime = "01/25/2024 14:30" // Format: YYYY-MM-DD HH:MM:SS

                    // Parse the future date and time
                    def dateFormat = new java.text.SimpleDateFormat("MM/dd/yyyy HH:mm")
                    Date futureDate = dateFormat.parse(futureDateTime)

                    // Get the current date and time
                    Date currentDate = new Date()

                    // Calculate the difference in milliseconds
                    long differenceInMillis = futureDate.time - currentDate.time

                    // Convert the difference to seconds
                    int differenceInSeconds = differenceInMillis / 1000
                    
                    // Example usage
                    setDelayedBuild(environment, region, params.InstanceNames, params.TicketNumber, 'Adhoc', hiddenParamUuidStr, differenceInSeconds)
                    
                }
            }
        }
        stage('CreateAMI') {
            when {
                expression { params.Mode == 'Adhoc'}
            }
            steps {
                script {

                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'rod_aws']]) {
                        withAWS(role: role, region: region, roleAccount: account, duration: '3600' ){

                            def ticketNumber = params.TicketNumber
                            
                            // validInstances = [
                            //     [id: 'TEST1', name: 'name1'],
                            //     [id: 'TEST', name: 'name2']
                            //     // Add more maps as needed
                            // ]

                            validInstances.each { instance ->
                                def instanceId = instance.id
                                def instanceName = instance.name

                                // Generate a three character, alphanumeric tag
                                def uuid = UUID.randomUUID()
                                def uuidString = uuid.toString()
                                def tag = uuidString[0..2]
                                
                                // Get UTC date
                                def utcDate = bat(script: 'powershell -command "[DateTime]::UtcNow.ToString(\'yyMMdd_HHmm\')"', returnStdout: true).trim()
                                utcDate = utcDate.readLines().drop(1).join("\n")

                                def amiName = "${ticketNumber}_${instanceName}_ADHOC_${utcDate}_${tag}"

                                echo "Creating AMI ${amiName} for ${instanceId}."

                                def awsCliCommand = "aws ec2 create-image --instance-id ${instanceId} --name ${amiName} --region ${region} --no-reboot --output json"

                                try {
                                    // Executes the AWS CLI command and does some post-processing.
                                    // The output includes the command at the top and can't be parsed so we have to drop the first line
                                    def cliOutput = bat(script: awsCliCommand, returnStdout: true).trim()
                                    cliOutput = cliOutput.readLines().drop(1).join("\n")
                                
                                    // Parse the CLI output as JSON
                                    def jsonSlurper = new groovy.json.JsonSlurper()
                                    def cliOutputJson = jsonSlurper.parseText(cliOutput)

                                    // Check if 'Reservations' is empty
                                    if (cliOutputJson.ImageId.isEmpty()) {
                                        unstable("No AMI ID returned for ${instanceName}. Moving on to next EC2 instance.")
                                        return
                                    }

                                    echo "Successfully created AMI ${cliOutputJson.ImageId}."
                                    
                                } catch (ex) {
                                    // Handle the error without failing the build
                                    unstable('Error in creating AMI. Moving on to next EC2 instance.')
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

def setDelayedBuild(environment, region, instanceNames, ticketNumber, mode, hiddenParam, delaySeconds) {
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
        new StringParameterValue('HiddenParam', hiddenParam)
    ]

    def future = job.scheduleBuild2(delaySeconds, new ParametersAction(params))
}