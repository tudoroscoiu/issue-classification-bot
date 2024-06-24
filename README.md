# 🤖 Issue Classification Bot

## Introduction
The *Issue Classification Bot* is a tool designed to automate the labeling of GitHub issues using machine learning (ML). It analyzes the content of issues (titles, descriptions), assigns relevant labels, and sends email notifications, facilitating easier issue tracking and management. This bot is particularly useful for large projects where manual issue tracking and categorization can be time-consuming.

## Requirements
- **Docker Compose installed** (check [installation guide](https://docs.docker.com/compose/install))
- **Smee CLI installed** (check [installation guide](https://github.com/probot/smee-client))
- **Storage:**
  + At least 14GB of storage available on your local machine:
      * 3GB for the bot files (including the weight files required by the ML model, see [Installation and Running Instructions](#installation-and-running-instructions))
      * at least 11GB for Docker Compose to create the Docker Images necessary to run the bot
 - **Ports Availability:**
     + Port 5001 on your local machine must be available
     + Port 8000 on your local machine must be available

## Installation and Running Instructions
1. Clone the repository to your local machine.
2. Add the following files to the local `/issue-classification-bot-2/Bot` directory:
  - `bot_key.pem`: containing the private key of the bot's GitHub App (find more information about private keys [here](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/managing-private-keys-for-github-apps))
  - `bot_email.secret`: containing the email address and the email password used by the bot to send notifications, structured as follows:
    * 1st line for the bot email address
    * 2nd line for the bot email password (app password, not the usual email password. For Google Accounts, find more information [here](https://support.google.com/mail/answer/185833?hl=en))
3. Download the [weight files](https://zenodo.org/records/7821209) required by the bot's ML model and add them to the local<br> `/issue-classification-bot-2/ModelsBackend/plugins/satd/SATD_Detector/data` directory as follows:
    * Rename `fasttext_issue_300.bin` to `embeddings.bin`
    * Rename `satd_detector_for_issues.hdf5` to `weights.hdf5`
4. Navigate to the root directory `/issue-classification-bot-2` containing the `docker-compose.yml` file.
5. Run the bot using the command:
   ```bash
   docker compose up
   ```
6. Open a new terminal window and run the following command, to automatically synchronize any future non-functional modifications to the bot's local files into its Docker container, while the bot is running:
   ```bash
   docker compose watch
   ```
7. Open a new terminal window and start the Smee CLI with:
   ```bash
   smee --url https://smee.io/Wpx6fSOaWjEaOK --path /webhook --port 5001
   ```

## Usage
Interact with the *Issue Classification Bot* by using the following commands in the comments of a GitHub issue:
- `/tdbot label`: Automatically labels an issue using the ML model.
- `/tdbot label <label>`: Manually labels an issue with the specified label.
- `/tdbot help`: Displays this help message with command details.

## Configuring the Bot
Edit the `Bot/config.json` file to configure the bot's behavior:
- `payload-type`: Choose between:
  * "title":       to set whether the bot's ML model should generate a label based on the title of the issue
  * "description": to set whether the bot's ML model should generate a label based on the description of the issue
  * "merged":      to set whether the bot's ML model should generate a single label based on the title and the description of the issue
  * "both":        to set whether the bot's ML model should generate two separate labels based on the title and the description of the issue
- `endpoint`: URL of the ML model's endpoint (*string*)
- `label-location`: JSON path in the ML model's response for the generated label (*string*)
- `auto-label`: *Boolean* to set if the bot should automatically label new issues
- `initial-message`: *Boolean* to set if the bot should create a comment message when an issue is created
- `send-emails`: *Boolean* to set if the bot should send email notifications
- `when-to-send`: Choose between:
  * "label":     to set whether the bot should send email notifications when an issue is labeled
  * "lingering": to set whether the bot should send email notifications when lingering issues have been identified in the repository
  * "all":       to set whether the bot should send email notifications for all the above scenarios
- `email-info`: Configuration options for the email sender
  - `which-labels`: if the bot should send email notifications when it adds a label to the issue (by setting `when-to-send` to "label" or "all"), choose between:
    * "all":      if the bot should send email notifications for all kinds of labels
    * "except":   if the bot should send email notifications for all kinds of labels except the ones specified in `except-labels`
    * "specific": if the bot should send email notifications only for the labels specified in `specific-labels`
  - `except-labels`: the labels for which the bot does not send email notifications, specified as a *list of strings*: \["label1", "label2", ...]
  - `specific-labels`: the labels for which the bot sends email notifications, specified as a *list of strings*: \["label1", "label2", ...]
  - `lingering-issue-threshold`: if the bot should send email notifications when lingering issues have been identified in the repository (by setting `when-to-send` to "lingering" or "all"), choose the threshold, in number of days (*integer*), after an issue would be considered lingering
  - `lingering-mode`: if the bot should send email notifications when lingering issues have been identified in the repository (by setting `when-to-send` to "lingering" or "all"), choose between:
    * "creation-date": if the bot should determine whether an issue is lingering or not based on the creation date of the issue
    * "last-modified": if the bot should determine whether an issue is lingering or not based on the last date when the issue has been modified (either by posting a comment, assigning a label, or any other kind of modification)
  - `recipients`: the list of email addresses of contributors that should receive email notifications, specified as a *list of strings*: \["emailAddress1", "emailAddress2", ...]
  - `email-body-template`: The template strings used for the body of the bot-generated emails
    * `label`: email body template (*string*) for email notifications about labels<br>
    **Any string that you use for this email body template can contain any of the following placeholders, which the bot replaces with actual data:**
      - **/issue_label**: the label added by the bot to the issue
      - **/issue_number**: the number of the issue where the bot added the label
      - **/issue_author**: the author of the issue where the bot added the label
      - **/issue_title**: the title of the issue where the bot added the label
      - **/issue_description**: the description of the issue where the bot added the label
      - **/issue_link**: the hyperlink to the issue where the bot added the label
      - **/issue_repository**: the repository of the issue where the bot added the label
      - **/issue_updated_at**: the date and time when the issue where the bot added the label was last updated
      - **/issue_created_at**: the date and time when the issue where the bot added the label was created
      #### Example:
      ```JSON
      "label": "Hi,\n\n/issue_label has been identified in issue #/issue_number with title: '/issue_title' and description: '/issue_description', created by @/issue_author in the /issue_repository repository.\nLink to the issue: /issue_link\n\nThis is an automated email. Replies to this message will not be read."
      ```
      will result in an email body in the following form: 
      
      > Hi,
      >
      > SATD has been identified in issue #4 with title: 'Test Issue' and description: 'Test Description', created by @user in the test-repo repository. <br>
      > Link to the issue: https://github.com/owner/test-repo/issues/4
      >
      > This is an automated email. Replies to this message will not be read.    
    * `lingering`: email body template for email notifications about lingering issues, specified as a *list of two strings*:<br>
        - 1st string in the list: main template string for the email body<br>
        **Any string that you use SHOULD contain one '{}' inside the string, for the lingering issues found in the repository.**
        - 2nd string in the list: template string for each of the lingering issues to be added to the email body<br> 
        **Any string that you use can contain any of the following placeholders, which the bot replaces with actual data:**
          - **/issue_number**: the number of the lingering issue
          - **/issue_author**: the author of the lingering issue
          - **/issue_title**: the title of the lingering issue
          - **/issue_description**: the description of the lingering issue
          - **/issue_link**: the hyperlink to the lingering issue
          - **/issue_repository**: the repository of the lingering issue
          - **/issue_updated_at**: the date and time when the lingering issue was last updated
          - **/issue_created_at**: the date and time when the lingering issue was created
        #### Example:
        ```JSON
        "lingering": [
          "Hi,\n\nThe following lingering issues have been identified:\n{}\nThis is an automated email. Replies to this message will not be read.",
          "- #/issue_number: '/issue_title'. The issue has been created on /issue_created_at, and it has been last modified on /issue_updated_at\n"
        ]
        ```
        will result in an email body in the following form:
        > Hi,
        >
        > The following lingering issues have been identified: <br>
        > \- #6: 'Test issue'. The issue has been created on 2024-04-13 17:25:13+00:00, and it has been last modified on 2024-04-25 16:40:12+00:00 <br>
        > \- #3: 'Another Test Issue'. The issue has been created on 2024-04-06 21:37:57+00:00, and it has been last modified on 2024-04-07 20:41:36+00:00
        >
        > This is an automated email. Replies to this message will not be read.
  - `email-subject-template`: the template strings used for the subject of the bot-generated emails
    * `label`:     email subject template (*string*) for email notifications about labels
    * `lingering`: email subject template (*string*) for email notifications about lingering issues
   
### Example `config.json`:
```JSON
{
  "payload-type": "description",
  "endpoint": "http://model:8000/models/Model1_IssueTracker_Li2022_ESEM",
  "label-location": "label",
  "auto-label": false,
  "initial-message": true,
  "send-emails": true,
  "when-to-send": "all",
  "email-info": {
    "which-labels": "specific",
    "except-labels": ["non-SATD"],
    "specific-labels": ["SATD"],
    "lingering-issue-threshold": 30,
    "lingering-mode": "last-modified",
    "recipients" : [
      "contributor1@gmail.com",
      "contributor2@yahoo.com"
    ],
    "email-body-template": {
      "label": "Hi,\n\n/issue_label has been identified in issue #/issue_number with title: '/issue_title' and description: '/issue_description', created by @/issue_author in the /issue_repository repository.\nLink to the issue: /issue_link\n\nThis is an automated email. Replies to this message will not be read.",
      "lingering": [
        "Hi,\n\nThe following lingering issues have been identified:\n{}\nThis is an automated email. Replies to this message will not be read.",
        "- #/issue_number: '/issue_title'. The issue has been created on /issue_created_at, and it has been last modified on /issue_updated_at\n"
      ]
    },
    "email-subject-template": {
      "label": "Technical debt identified",
      "lingering": "Lingering issues identified"
    }
  }
}
```
## Troubleshooting
If you encounter issues with the bot:
- If labels are not being assigned to issues when a `/tdbot label` comment is posted:
  * Verify that the `config.json` file is located both in the local `/issue-classification-bot-2/Bot` directory, and in the `repository/Bot` directory of the repositories that have the bot's GitHub App installed, and that it is [set up correctly](#configuring-the-bot).
  * Verify that the Smee CLI is running and properly connected.
  * Verify that the generated label is not already assigned to the issue.
- If bot email notifications are not being sent/received:
  * Verify that the `config.json` file is located both in the local `/issue-classification-bot-2/Bot` directory, and in the `repository/Bot` directory of the repositories that have the bot's GitHub App installed, and that it is [set up correctly](#configuring-the-bot).
  * Verify that the Smee CLI is running and properly connected.
  * Verify that the `bot_email.secret` file is stored in the local `/issue-classification-bot-2/Bot` directory, and that it is [set up correctly](#installation-and-running-instructions).

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Contact
For questions or feedback regarding the Issue Classification Bot, please open an issue in the GitHub repository.

## Acknowledgments
Special thanks to all contributors and maintainers of this project. Your efforts greatly enhance its quality and usability.
