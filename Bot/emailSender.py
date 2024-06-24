import smtplib

from email.mime.text import MIMEText

"""
Read the bot email info from a "bot_email.secret" file structured as follows:
- 1st line for the bot email address
- 2nd line for the bot email password (app password, not the usual email password)
"""
with open("bot_email.secret", "r") as secret_file:
    lines = secret_file.read().splitlines()

bot_email_address = lines[0]
bot_email_password = lines[1]
# This is the name that we want to be displayed as the sender to the recipients, instead of the actual bot email address
bot_name = 'Issue Classification Bot'
email_server = 'smtp.gmail.com'
email_server_port = 465


# Template string formatting function for replacing placeholders with actual data
def format_template(issue, template, label_or_feature=None):
    """
    Also handling the edge case where some issues might not have a description (body), but the template string specified
    in the Bot/config.json for lingering issues uses the /issue_description placeholder, in which case the placeholder
    will be replaced with the empty string in the generated email body, to avoid any errors.
    """
    formatted_template = (template.replace('/issue_number', str(issue.number))
                                  .replace('/issue_author', issue.user.login)
                                  .replace('/issue_title', issue.title)
                                  .replace('/issue_description', issue.body or "")
                                  .replace('/issue_link', issue.html_url)
                                  .replace('/issue_repository', issue.repository.name)
                                  .replace('/issue_updated_at', str(issue.updated_at))
                                  .replace('/issue_created_at', str(issue.created_at)))
    if label_or_feature is not None:
        formatted_template = (formatted_template.replace('/issue_label', label_or_feature)
                                                .replace('/feature', label_or_feature))

    return formatted_template


# Prepare email content for label case
def prepare_label_email(issue_list, email_info, label):
    # Obtain the email body and email subject templates for emails concerning bot-generated labels
    body = email_info['email-body-template']['label']
    subject = email_info['email-subject-template']['label']
    # Obtain the relevant issue (and the only one) from the provided list of issues
    issue = issue_list[0]
    # Replace placeholders in the email body template with actual data from the label and issue
    formatted_body = format_template(issue, body, label)
    # MIMEText used to create the email object
    return MIMEText(formatted_body), subject


# Prepare email content for lingering case
def prepare_lingering_email(issue_list, email_info):
    # Obtain the email body and email subject templates for emails concerning lingering issues identified by the bot
    body_main = email_info['email-body-template']['lingering'][0]
    body_issue = email_info['email-body-template']['lingering'][1]
    subject = email_info['email-subject-template']['lingering']
    # Replace placeholders in the lingering issue template with actual data from the issue, for each of the lingering issues identified by the bot
    formatted_body_issues = "".join([format_template(issue, body_issue) for issue in issue_list])
    # Replace the '{}' in the main template string for the email body with the string above
    formatted_body_main = body_main.format(formatted_body_issues)
    # MIMEText used to create the email object
    return MIMEText(formatted_body_main), subject


# Prepare email content for feature under development case
def prepare_feature_email(issue_list, email_info):
    # Obtain the email body and email subject templates for emails concerning the feature under development
    body = email_info['email-body-template']['feature']
    subject = email_info['email-subject-template']['feature']
    feature = email_info['feature-under-development']
    # Obtain the relevant issue (and the only one) from the provided list of issues
    issue = issue_list[0]
    # Replace placeholders in the email body template with actual data from the feature and issue
    formatted_body = format_template(issue, body, feature)
    # MIMEText used to create the email object
    return MIMEText(formatted_body), subject


# Mail sending function
def send_email(issue_list, config, case, label=None):
    email_info = config['email-info']
    recipients = email_info['recipients']

    try:
        # Establish the SMTP connection to specified server over a secure SSL connection
        smtp = smtplib.SMTP_SSL(email_server, email_server_port)
        # Log in on the SMTP server using the specified bot email address and bot email password
        smtp.login(bot_email_address, bot_email_password)
    except smtplib.SMTPAuthenticationError as e:
        print("SMTP authentication error:", e, flush=True)
        return
    except Exception as e:
        print("Authentication error:", e, flush=True)
        return

    """
    Create the email message for a label:
    - if the practitioner wants to receive any kind of label generated by the ML model for the issue (by setting the
      "which-labels" field to "all" in the Bot/config.json file)
    OR
    - if the generated label is not contained in the list associated with the "except-labels" field (also specified 
      by the practitioner), when the practitioner sets the "which-labels" field to "except" in the Bot/config.json 
      file
    OR
    - if the generated label is contained in the list associated with the "specific-labels" field (also specified 
      by the practitioner), when the practitioner sets the "which-labels" field to "specific" in the Bot/config.json 
      file
    """
    # Label case
    if case == 0:
        if (email_info["which-labels"] == "all"
                or (email_info["which-labels"] == "except" and label not in email_info["except-labels"])
                or (email_info["which-labels"] == "specific" and label in email_info["specific-labels"])):
            email, subject = prepare_label_email(issue_list, email_info, label)
        else:
            if email_info["which-labels"] == "except":
                print(f"Generated label: {label} is contained in the 'except-labels' list specified in config.json,"
                      " no email sent", flush=True)
            if email_info["which-labels"] == "specific":
                print(f"Generated label: {label} is not contained in the 'specific-labels' list specified in config.json,"
                      " no email sent", flush=True)
            # Close the SMTP connection since no email will be sent
            smtp.quit()
            return

    """
    Create the email message for lingering issues
    """
    # Lingering case
    if case == 1:
        email, subject = prepare_lingering_email(issue_list, email_info)

    """
    Create the email message for a feature under development:
    - if the practitioner manually assigns a label to an issue (using "/tdbot label <label>"), and the label matches the 
      feature under development specified in the "feature-under-development" field of the Bot/config.json file
    OR
    - if the practitioner creates a new issue, and the feature under development (specified in the 
      "feature-under-development" field of the Bot/config.json file) is mentioned inside the issue body
    """
    # Feature under development case
    if case == 2:
        issue = issue_list[0]
        if label:
            if label == email_info["feature-under-development"]: # IDEA: or email_info["feature"] in label, in case the feature can be a substring of the label
                email, subject = prepare_feature_email(issue_list, email_info)
            else:
                print(f"Recently added label: {label} to issue #{issue.number} does not mention the feature under "
                      "development, no email sent", flush=True)
                # Close the SMTP connection since no email will be sent
                smtp.quit()
                return
        else:
            # Case-insensitive check if the feature under development is contained in the body of the issue
            if issue.body is not None and email_info["feature-under-development"].lower() in issue.body.lower():
                email, subject = prepare_feature_email(issue_list, email_info)
            else:
                print(f"Newly created issue #{issue.number} does not mention the feature under development in its body"
                      " no email sent", flush=True)
                # Close the SMTP connection since no email will be sent
                smtp.quit()
                return

    email['From'] = bot_name
    email['To'] = ', '.join(recipients)
    email['Subject'] = subject

    # After the email is created, send it using the SMTP connection to the specified recipients; also error handling
    try:
        smtp.sendmail(bot_email_address, recipients, email.as_string())
        print("Email sent successfully!", flush=True)
    except smtplib.SMTPException as error:
        print(f"SMTP mail sending error: {error}", flush=True)
    except Exception as error:
        print(f"Mail sending error: {error}", flush=True)

    # Close the SMTP connection after sending the email(s)
    smtp.quit()
    