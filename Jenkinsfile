properties([
    parameters([
        choice(
            name: 'Environment',
            choices: ['rod_aws','rod_aws_2','Global-OSS'],
        ),
        text(
            name: 'InstanceNames', 
            defaultValue: 'APSPTEST1\nAPSPTEST2\nAPSPTEST3',
        ),
        string(
            name: 'TicketNumber',
            defaultValue: 'SCTASK00000000',
        ),
        choice( 
            name: 'Mode',
            choices: ['On-Demand','Scheduled'] //,'Express'],
        ),
        [$class: 'DynamicReferenceParameter',
            choiceType: 'ET_FORMATTED_HTML',
            omitValueField: true,
            name: 'Date',
            referencedParameters: 'Mode',
            script: [
                $class: 'GroovyScript',
                script: [
                    classpath: [],
                    sandbox: false,
                    script:
                    """
if (Mode.equals("Scheduled")) {
    return "<input type='text' name='value' value='Enter date in MM/DD/YYYY format' class=\\"jenkins-input\\" onclick='this.value=\\"\\";'/>"
}
else {
    return "<input type='text' name='value' value='N/A' disabled class=\\"jenkins-input\\" style='color: grey;'/>"
}
                    """
                ]
            ]
        ],
        [$class: 'DynamicReferenceParameter',
            choiceType: 'ET_FORMATTED_HTML',
            omitValueField: true,
            name: 'Time',
            referencedParameters: 'Mode',
            script: [
                $class: 'GroovyScript',
                script: [
                    classpath: [],
                    sandbox: false,
                    script:
                    """
if (Mode.equals("Scheduled")) {
    return "<input type='text' name='value' value='Enter time in military time format. e.g. 23:00' class=\\"jenkins-input\\" onclick='this.value=\\"\\";'/>"
}
else {
    return "<input type='text' name='value' value='N/A' disabled class=\\"jenkins-input\\" style='color: grey;'/>"
}
                    """
                ]
            ]
        ],
    ])
])

import java.util.UUID
import groovy.json.JsonSlurperClassic
import groovy.json.JsonOutput


class RegionCode {
    String code
    String region
}

class InstanceDetails {
    String instanceName
    String instanceId
    String region
}

class AMIDetails {
    InstanceDetails instanceDetails  // Embedding InstanceDetails class
    String amiName
    String amiId
    String status

    // Constructor to initialize all fields
    AMIDetails(InstanceDetails instanceDetails, String amiName, String amiId, String status) {
        this.instanceDetails = instanceDetails
        this.amiName = amiName
        this.amiId = amiId
        this.status = status
    }

    // Optional: toString method for easy printing
    @Override
    String toString() {
        return "AMI Details: [AMI Name: ${amiName}, AMI ID: ${amiId}, Instance Details: [Instance Name: ${instanceDetails.instanceName}, Instance ID: ${instanceDetails.instanceId}, Region: ${instanceDetails.region}]]"
    }
}

// Function to find region by prefix for GOSS
def findRegionGOSS(String instanceName, List<RegionCode> regionCodes) {
    if (instanceName.length() >= 8) { 
        // Make sure instanceName has at least 8 characters
        String substring = instanceName.substring(4, 8); // Extract the 5th to 8th characters
        for (RegionCode regionCode : regionCodes) {
            if (substring.equalsIgnoreCase(regionCode.code)) {
                return regionCode.region;
            }
        }
    }
    return null; // Return null if no match is found or if instanceName is too short
}

// Function to find region by prefix for non-goss AWS accounts
def findRegionNonGOSS(String instanceName, List<RegionCode> regionCodes) {
    for (regionCode in regionCodes) {
        if (instanceName.toUpperCase().startsWith(regionCode.code)) {
            return regionCode.region
        }
    }
    return null // Return null if no match is found
}

def queueAMICreation(amiCreationRequestId, account, instanceNames, instanceIDs, region, ticketNumber, mode,  date, time, secondsFromNow) {
    // def job = Hudson.instance.getJob('AMICreationPipeline')
    def job = Jenkins.instance.getItemByFullName('AMICreationPipeline')

    if (job == null) {
        throw new IllegalStateException("Job not found: AMICreationPipeline")
    }

    def params = [
        new StringParameterValue('Account', account),
        new StringParameterValue('InstanceNames', instanceNames),
        new StringParameterValue('InstanceIDs', instanceIDs),
        new StringParameterValue('Region', region),
        new StringParameterValue('TicketNumber', ticketNumber),
        new StringParameterValue('Mode', mode),
        new StringParameterValue('Date', date),
        new StringParameterValue('Time', time),
        new StringParameterValue('AmiCreationRequestId', amiCreationRequestId)
    ]

    def future = job.scheduleBuild2(secondsFromNow, new ParametersAction(params))
}

// Function to check if the file exists and is not empty
def boolean fileExistsAndNotEmpty(String filePath) {
    new File(filePath).with { file ->
        file.exists() && file.length() > 0
    }
}

// The new method to add an object to the queue
void createAMICreationRequest(Object newAMICreationRequest, String amiCreationDBPath) {
    def objectsList = []

    if (fileExistsAndNotEmpty(amiCreationDBPath)) {
        try {
            def existingContent = new File(amiCreationDBPath).text
            def jsonSlurperClassic = new JsonSlurperClassic()
            objectsList = jsonSlurperClassic.parseText(existingContent)
        } catch (Exception e) {
            println("Unable to parse json file. Please check for syntax errors.")
            return // Exit the method if there's a parsing error
        }
    }

    // Add the new object to the list
    objectsList << newAMICreationRequest

    // Convert the list back to JSON string and pretty print it
    def newJsonStr = JsonOutput.toJson(objectsList)
    def prettyJsonStr = JsonOutput.prettyPrint(newJsonStr)

    // Write the JSON string back to the file
    writeFile(file: amiCreationDBPath, text: prettyJsonStr)
}


void sendEmailNotification (Object AMICreationRequest) {
    def body = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    body {
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0 20px;
        box-sizing: border-box;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 0.9em;
        min-width: 400px;
        border-radius: 5px 5px 0 0;
        overflow: hidden;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
    }
    thead tr {
        background-color: #005B9A; /* Deltek's blue */
        color: #ffffff;
        text-align: left;
    }
    th, td {
        padding: 12px 15px;
    }
    tbody tr {
        border-bottom: 1px solid #dddddd;
    }

    tbody tr:nth-of-type(even) {
        background-color: #f0f0f0; /* Light gray for better readability */
    }

    tbody tr:last-of-type {
        border-bottom: 2px solid #005B9A;
    }

    tbody tr.active-row {
        font-weight: bold;
        color: #005B9A;
    }
    .status-message {
        margin-top: 20px;
        font-size: 0.9em;
        color: #333; /* Dark gray for the message */
    }
</style>
</head>
<body>

<! -- <p class="status-message">AMI(s) have been successfully created in AWS environment ${environment}. Reference ticket: ${TicketNumber}</p> -->


<table>
    <thead>
        <tr>
            <th>Region</th>
            <th>Instance ID</th>
            <th>InstanceName</th>
            <th>AMI ID</th>
            <th>AMI Name</th>
            <th>Status</th>
        </tr>
    </thead>
    <tbody>
"""
                        AMICreationRequest.AMIs.each { AMI ->
                            body += """
        <tr>
            <td>${AMI.instanceDetails.region}</td>
            <td>${AMI.instanceDetails.instanceId}</td>
            <td>${AMI.instanceDetails.instanceName}</td>
            <td>${AMI.amiId}</td>
            <td>${AMI.amiName}</td>
            <td>${AMI.status}</td>
        </tr>
                            """
                        }

                        // Close the table
                        body += """
    </tbody>
</table>
</body>
</html>
""" 

                        // Send the email using the email-ext plugin, including the table
                        emailext(
                            subject: "AMI Creation Report",
                            body: body,
                            mimeType: 'text/html',
                            to: 'recipient@example.com'
                        )
}

// Variables used in 'GetEnvironmentDetails' stage
def environment = ""
def account = ""
def role = 'AMICreationRole'
def amiCreationRequestId = ""

// Variables used in 'ValidateEC2' stage
def validInstances = []
def createdAMIs = []

// Variables used in 'ValidateSchedule' and 'ScheduleAMICreation' stages
String executionDateTimeStr = ""
int secondsFromNow = 0
boolean isImminentExecution = false
def amiCreationDBPath = 'C:\\code\\AMICreationQueueService\\Test.json'

def regionCodesGoss = [
    new RegionCode(code: "ASE1", region: "ap-southeast-1"),
    new RegionCode(code: "ASE2", region: "ap-southeast-2"),
    new RegionCode(code: "CAC1", region: "ca-central-1"),
    new RegionCode(code: "EUC1", region: "eu-central-1"),
    new RegionCode(code: "EUW1", region: "eu-west-1"),
    new RegionCode(code: "USE1", region: "us-east-1"),
    new RegionCode(code: "USW2", region: "us-west-2")
]

def regionCodesNonGoss = [
    new RegionCode(code: "USEA", region: "us-east-1"),
    new RegionCode(code: "USWE", region: "us-west-1"),
    new RegionCode(code: "EUCE", region: "eu-central-1"),
    new RegionCode(code: "EUWE", region: "eu-west-1"),
    new RegionCode(code: "APAU", region: "ap-southeast-2"),
    new RegionCode(code: "APSP", region: "ap-southeast-1"),
    new RegionCode(code: "UOUE", region: "us-east-1"),
    new RegionCode(code: "UOUW", region: "us-west-1"),
    new RegionCode(code: "CACE", region: "ca-central-1")
]

pipeline {

    agent any

    stages {
        stage('GetEnvironmentDetails') {
            when {
                expression { params.Mode != 'Express'}
            }
            steps {
                script {
                    environment = params.Environment

                    switch (environment) {
                        case 'rod_aws':
                            account = '554249804926'
                            break
                        case 'rod_aws_2':
                            account = '992382788789'
                            break
                        case 'Global-OSS':
                            account = '554249804926'
                            break
                        default:
                            error("No matching environment details found that matches \"${environment}\".")
                    }

                    echo "Successfully retrieved environment details for environment \"${environment}\"."                   

                }
            }

        }
        stage('ValidateEC2') {
            when {
                expression { params.Mode != 'Express'}
            }
            steps {
                script {

                    // removes whitespaces from instance names and splits them
                    def instanceNames = params.InstanceNames.split('\n')
                    def invalidInstanceNames = []

                    if (environment == "Global-OSS") {
                        // Populate valid and invalid instances arrays
                        instanceNames.each { instanceName ->
                            def region = findRegionGOSS(instanceName, regionCodesGoss)
                            if (region) {
                                validInstances << new InstanceDetails(instanceName: instanceName, region: region)
                            } else {
                                invalidInstanceNames << instanceName
                            }
                        }
                    }
                    else if (environment != "Global-OSS") {
                        // Populate valid and invalid instances arrays
                        instanceNames.each { instanceName ->
                            def region = findRegionNonGOSS(instanceName, regionCodesNonGoss)
                            if (region) {
                                validInstances << new InstanceDetails(instanceName: instanceName, region: region)
                            } else {
                                invalidInstanceNames << instanceName
                            }
                        }
                    }

                    // Exit the pipeline if there are no valid instances
                    if (validInstances.isEmpty()) {
                        error("Unable to identify a region for all instances. Please verify that the correct account alias and EC2 instance names have been entered. Exiting the pipeline.")
                    }

                    if (invalidInstanceNames) {
                        unstable("Unable to identify a region for the following instances. Please verify that the correct account alias and EC2 instance names have been entered: ${invalidInstanceNames.join(', ')}")
                    }

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
                    validInstances = validInstances.findAll { it.instanceId }

                    // Exit the pipeline if there are no valid instances
                    if (validInstances.isEmpty()) {
                        error("None of the instances entered exists. Please verify that the correct account alias and EC2 instance names have been entered. Exiting the pipeline.")
                    }

                }
            }
        }
        stage('ValidateSchedule') {
            when {
                expression { params.Mode == 'Scheduled'}
            }
            steps {
                script {

                     // Specify the future date and time in military time (24-hour format)
                    // e.g. "01/27/2024 14:25"
                    executionDateTimeStr = params.Date.split(',').first() + ' ' + params.Time.split(',').first()

                    Date executionDate = null

                    try {
                        // Parse the future date and time
                        def dateFormat = new java.text.SimpleDateFormat("MM/dd/yyyy HH:mm")
                        executionDate = dateFormat.parse(executionDateTimeStr)
                    }
                    catch (ex) {
                        // Handle the error without failing the build
                        error("Unable to parse DateTime ${executionDateTimeStr}.")
                    }
                    
                    // Get the current date and time
                    Date currentDate = new Date()

                    // Calculate the difference in milliseconds
                    long differenceInMillis = executionDate.time - currentDate.time

                    // Convert the difference to seconds
                    secondsFromNow = differenceInMillis / 1000

                    if (secondsFromNow < 0) {
                        error ("Scheduled date must be in a future date.")
                    }

                    echo "Scheduled date ${executionDateTimeStr} is valid."

                    if (secondsFromNow <= 900) {
                        isImminentExecution = true
                        echo "Requested date identified as imminent execution (within 15 minutes)."
                    }

                }
            }
        }
        stage('ScheduleAMICreation') {
            when {
                expression { params.Mode == 'Scheduled'}
            }
            steps {
                script {

                    // Group instances by region
                    def instancesByRegion = validInstances.groupBy { it.region }

                    // Iterate over each region and verify instances
                    instancesByRegion.each { region, instances ->
                        // We will set a unique valued parameter so manual triggered builds with the same parameters will not override the scheduled build
                        amiCreationRequestId = UUID.randomUUID()
                        amiCreationRequestId = amiCreationRequestId.toString()

                        def AMIs = []
                        instances.each { instance ->
                            def amiDetails = new AMIDetails(instance, '', '', '')
                            AMIs << amiDetails

                        }

                        def amiCreationRequestObj = [
                            'AmiCreationRequestId': amiCreationRequestId,
                            'Status': 'Scheduled',
                            'Account': account,
                            'Region': region,
                            'AMIs': AMIs,
                            'TicketNumber': params.TicketNumber,
                            'Date': params.Date,
                            'Time': params.Time,
                            'Mode': 'Express',
                            
                        ]

                        
                        String instanceNames = amiCreationRequestObj.AMIs.collect { it.instanceDetails.instanceName }.join(',')
                        String instanceIds = amiCreationRequestObj.AMIs.collect { it.instanceDetails.instanceId }.join(',')

                        // Puts imminent AMI Creation request for execution
                        if (isImminentExecution) { 
                            queueAMICreation(amiCreationRequestId, account, instanceNames, instanceIds, region, params.TicketNumber, 'Express', params.Date, params.Time, secondsFromNow)

                            amiCreationRequestObj.Status = 'QueuedForExecution'
                        }
                        
                        // Puts request in AMICreationDB as PendingCreation
                        createAMICreationRequest(amiCreationRequestObj, amiCreationDBPath)                       
                        
                        def newScheduledAMICreationObjStr = "Successfully scheduled AMI Creation:\n"
                        newScheduledAMICreationObjStr += "AmiCreationRequestId: ${amiCreationRequestObj.AmiCreationRequestId}\n"
                        newScheduledAMICreationObjStr += "Account: ${amiCreationRequestObj.Account}\n"
                        newScheduledAMICreationObjStr += "Region: ${amiCreationRequestObj.Region}\n"
                        newScheduledAMICreationObjStr += "InstanceNames: ${instanceNames}\n"
                        newScheduledAMICreationObjStr += "InstanceIDs: ${instanceIds}\n"
                        newScheduledAMICreationObjStr += "TicketNumber: ${amiCreationRequestObj.TicketNumber}\n"
                        newScheduledAMICreationObjStr += "Date: ${amiCreationRequestObj.Date}\n"
                        newScheduledAMICreationObjStr += "Time: ${amiCreationRequestObj.Time}\n"
                    
                        echo "${newScheduledAMICreationObjStr}"

                        // SEND EMAIL
                        sendEmailNotification(amiCreationRequestObj)

                    }
  
                }
            }
        }
        stage('CreateAMI') {
            when {
                expression { params.Mode == 'On-Demand' || params.Mode == 'Express' }
            }
            steps {
                script {

                    // Generates validInstances array directly from parameters
                    if (params.Mode == 'Express') {
                        def instanceNames = params.InstanceNames.replaceAll("\\s+", "").split(',')
                        def instanceIDs =  params.InstanceIDs.replaceAll("\\s+", "").split(',')

                        if (instanceNames.length != instanceIDs.length) {
                            error ("The count of Instances names and IDs does not match.")
                        }
                        
                        for (int i = 0; i < instanceNames.length; i++) {
                            
                            validInstances << new InstanceDetails(instanceName: instanceNames[i], instanceId: instanceIDs[i], region: params.Region)
                        }

                        // Gets AWS account number from paramters
                        account = params.Account
                        amiCreationRequestId = params.AmiCreationRequestId

                    }

                    // Displays a summary of valid EC2 instances
                    if (!validInstances.isEmpty()) {
                        def validInstancesStr = "Final list of instances:\n"
                        validInstancesStr += "-----------------------\n"
                        validInstances.each { instance ->
                            validInstancesStr += "Instance Name: ${instance.instanceName}\n"
                            validInstancesStr += "Instance ID: ${instance.instanceId}\n"
                            validInstancesStr += "Region: ${instance.region}\n"
                            validInstancesStr += "-----------------------\n"
                        }

                        echo "${validInstancesStr}"
                    }                    

                    // Group instances by region
                    def instancesByRegion = validInstances.groupBy { it.region }

                    // Iterate over each region and verify instances
                    instancesByRegion.each { region, instances ->
                        withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'rod_aws']]) {
                            withAWS(role: role, region: region, roleAccount: account, duration: '3600' ){

                                def ticketNumber = params.TicketNumber
                                
                                // validInstances = [
                                //     [id: 'TEST1', name: 'name1'],
                                //     [id: 'TEST', name: 'name2']
                                //     // Add more maps as needed
                                // ]
                                
                                def AMIs = []

                                instances.each { instance ->
                                    def instanceId = instance.instanceId
                                    def instanceName = instance.instanceName

                                    // echo "${instanceName}: ${instanceId}"

                                    // Generate a three character, alphanumeric tag
                                    def uuid = UUID.randomUUID()
                                    def uuidString = uuid.toString()
                                    def tag = uuidString[0..2]
                                    
                                    Date currentDate = new Date()
                                    def dateFormat = new java.text.SimpleDateFormat("MMddyyyy_HHmm")
                                    def currentDateStr = dateFormat.format(currentDate)

                                    def amiName = "${ticketNumber}_${instanceName}_${currentDateStr}_${tag}"

                                     // echo "Creating AMI ${amiName} for ${instanceId}."

                                    def awsCliCommand = "aws ec2 create-image --instance-id ${instanceId} --name ${amiName} --region ${region} --no-reboot --output json"

                                    try {
                                        // Executes the AWS CLI command and does some post-processing.
                                        // The output includes the command at the top and can't be parsed so we have to drop the first line
                                        def cliOutput = bat(script: awsCliCommand, returnStdout: true).trim()
                                        cliOutput = cliOutput.readLines().drop(1).join("\n")
                                    
                                        // Parse the CLI output as JSON
                                        def jsonSlurper = new groovy.json.JsonSlurper()
                                        def cliOutputJson = jsonSlurper.parseText(cliOutput)

                                        amiID = cliOutputJson.ImageId
                                        // Check if 'ImageId' is empty
                                        if (amiID.isEmpty()) {
                                            unstable("No AMI ID returned for ${instanceId} - ${instanceName}. Moving on to next EC2 instance.")
                                            return
                                        }

                                        echo "Successfully created AMI ${amiID} - ${amiName} for ${instanceId} - ${instanceName}."

                                        // def amiDetails = new AMIDetails(instance, amiName, cliOutputJson.ImageId)

                                        def amiDetails = new AMIDetails(instance, amiName, amiID, 'Pending')
                                        
                                        AMIs << amiDetails
                                        
                                    } catch (ex) {
                                        // Handle the error without failing the build

                                        def amiDetails = new AMIDetails(instance, '', '', 'Failed')
                                        
                                        AMIs << amiDetails

                                        unstable("Error in creating AMI for ${instanceId} - ${instanceName}. Moving on to next EC2 instance.")
                                    }
                                }

                                if (params.Mode == 'On-Demand') {
                                    amiCreationRequestId = UUID.randomUUID()
                                    amiCreationRequestId = amiCreationRequestId.toString()

                                    def amiCreationRequestObj = [
                                        'AmiCreationRequestId': amiCreationRequestId,
                                        'Status': 'AwaitingAvailability',
                                        'Account': account,
                                        'Region': region,
                                        'AMIs': AMIs,
                                        'TicketNumber': ticketNumber,
                                        // 'Date': params.Date,
                                        // 'Time': params.Time,
                                        'Mode': params.Mode,
                                    ]

                                    createAMICreationRequest(amiCreationRequestObj, amiCreationDBPath)

                                    // SEND EMAIL
                                    sendEmailNotification(amiCreationRequestObj)
                                }
                                else if (params.Mode == 'Express') {
                                    
                                    def objectsList = []

                                    if (fileExistsAndNotEmpty(amiCreationDBPath)) {
                                        try {
                                            def existingContent = new File(amiCreationDBPath).text
                                            def jsonSlurperClassic = new JsonSlurperClassic()
                                            objectsList = jsonSlurperClassic.parseText(existingContent)
                                        } catch (Exception e) {
                                            println("Unable to parse json file. Please check for syntax errors.")
                                            return // Exit the method if there's a parsing error
                                        }
                                    }

                                    def amiCreationRequestObj = objectsList.find { it.AmiCreationRequestId == amiCreationRequestId }
                                    amiCreationRequest.Status = 'AwaitingAvailability'

                                    AMIs.each { newAMI ->
                                        def amiDataFromDB = amiCreationRequestObj.AMIs.find { it.instanceDetails.instanceId == newAMI.instanceDetails.instanceId}

                                        amiDataFromDB.amiId = newAMI.amiId
                                        amiDataFromDB.amiName = newAMI.amiName
                                        amiDataFromDB.status = 'Pending'

                                    }

                                    // Convert the list back to JSON string and pretty print it
                                    def newJsonStr = JsonOutput.toJson(objectsList)
                                    def prettyJsonStr = JsonOutput.prettyPrint(newJsonStr)

                                    // Write the JSON string back to the file
                                    writeFile(file: amiCreationDBPath, text: prettyJsonStr)

                                    // SEND EMAIL
                                    sendEmailNotification(amiCreationRequestObj)
                                }
                            }
                        }
                    }
                }
            }
        }
//         stage('Send Notification') {
//             steps {
//                 script {
//                     if (params.Mode == 'Scheduled') {

//                     }
//                     else {
//                         def body = """
// <!DOCTYPE html>
// <html lang="en">
// <head>
// <meta charset="UTF-8">
// <meta name="viewport" content="width=device-width, initial-scale=1.0">
// <style>
//     body {
//         font-family: Arial, sans-serif;
//         margin: 0;
//         padding: 0 20px;
//         box-sizing: border-box;
//     }
//     table {
//         width: 100%;
//         border-collapse: collapse;
//         margin: 25px 0;
//         font-size: 0.9em;
//         min-width: 400px;
//         border-radius: 5px 5px 0 0;
//         overflow: hidden;
//         box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
//     }
//     thead tr {
//         background-color: #005B9A; /* Deltek's blue */
//         color: #ffffff;
//         text-align: left;
//     }
//     th, td {
//         padding: 12px 15px;
//     }
//     tbody tr {
//         border-bottom: 1px solid #dddddd;
//     }

//     tbody tr:nth-of-type(even) {
//         background-color: #f0f0f0; /* Light gray for better readability */
//     }

//     tbody tr:last-of-type {
//         border-bottom: 2px solid #005B9A;
//     }

//     tbody tr.active-row {
//         font-weight: bold;
//         color: #005B9A;
//     }
//     .status-message {
//         margin-top: 20px;
//         font-size: 0.9em;
//         color: #333; /* Dark gray for the message */
//     }
// </style>
// </head>
// <body>

// <p class="status-message">AMI(s) have been successfully created in AWS environment ${environment}. Reference ticket: ${TicketNumber}</p>


// <table>
//     <thead>
//         <tr>
//             <th>Region</th>
//             <th>Instance ID</th>
//             <th>InstanceName</th>
//             <th>AMI ID</th>
//             <th>AMI Name</th>
//         </tr>
//     </thead>
//     <tbody>
// """
//                         createdAMIs.each { detail ->
//                             body += """
//         <tr>
//             <td>${detail.instanceDetails.region}</td>
//             <td>${detail.instanceDetails.instanceId}</td>
//             <td>${detail.instanceDetails.instanceName}</td>
//             <td>${detail.amiId}</td>
//             <td>${detail.amiName}</td>
//         </tr>
//                             """
//                         }

//                         // Close the table
//                         body += """
//     </tbody>
// </table>
// </body>
// </html>
// """ 

//                         // Send the email using the email-ext plugin, including the table
//                         emailext(
//                             subject: "AMI Creation Report",
//                             body: body,
//                             mimeType: 'text/html',
//                             to: 'recipient@example.com'
//                         )
//                     }
//                 }
//             }
//         }
        // stage('CleanUp') {
        //     when {
        //         expression { params.Mode == 'Express'}
        //     }

        //     steps {
        //         script {
        //             // Initialize an empty list for the objects
        //             def objectsList = []

        //             // Check if the file exists
        //             if (fileExistsAndNotEmpty(amiCreationDBPath)) {
        //                 // File exists and is not empty, read the existing content
        //                 def existingContent = new File(amiCreationDBPath).text
        //                 def jsonSlurperClassic = new JsonSlurperClassic()

        //                 // Try to parse the existing content, handle potential parsing errors
        //                 try {
        //                     objectsList = jsonSlurperClassic.parseText(existingContent)
        //                 } catch (Exception e) {

        //                     error ("Unable to parse json file. Please check for syntax errors.")
        //                 }
        //             }

        //             // Filter the array to remove the object with the specified ID
        //             currentScheduledBuild = objectsList.findAll { it.AmiCreationRequestId == amiCreationRequestId }

        //             if (!currentScheduledBuild) {
        //                 echo "Scheduled AMI creation request not found queue file. The request must either be imminent (within 15 mins) or it has been manually deleted."
        //             }
        //             else {
        //                 // Filter the array to remove the object with the specified ID
        //                 objectsList = objectsList.findAll { it.AmiCreationRequestId != amiCreationRequestId }

        //                 // Convert the list back to JSON string
        //                 def newJsonStr = JsonOutput.toJson(objectsList)
        //                 def prettyJsonStr = JsonOutput.prettyPrint(newJsonStr)

        //                 // Write the JSON string back to the file
        //                 writeFile(file: amiCreationDBPath, text: prettyJsonStr)

        //                 echo "Successfully fulfilled scheduled AMI Creation Request with build ID ${amiCreationRequestId}."
        //             }                   
        //         }
        //     }
            
        // }
    }
}