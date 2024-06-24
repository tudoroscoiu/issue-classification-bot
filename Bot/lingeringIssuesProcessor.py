import json
import base64
import pytz # Used for timezone handling

from github import Github, GithubIntegration
from datetime import datetime
from emailSender import send_email

"""
* Function to determine the last time an issue has been modified (by a user, not by the bot), either by creating a 
  comment on it or some other type of event.
* It could be the case that the issue has not been touched since it has been created, so the time of last modification
  would be, in this case, the time when the issue has been created.
"""
def issue_last_modified(issue):
    dates = [issue.created_at]
    for event in issue.get_events():
        if (not event.actor) or (event.actor.login != "issue-classification-bot[bot]"):
            dates.append(event.created_at)
    for comment in issue.get_comments():
        if comment.user.login != "issue-classification-bot[bot]":
            dates.append(comment.created_at)
    return max(dates)


"""
* Function to obtain the installation IDs of the bot's GitHub App, together with the owners and repositories where it is 
  installed.
* This function is called every time the processing of lingering issues is scheduled, in order to obtain the most recent
  list of installations, and to allow practitioners to install/unsuspend or uninstall/suspend the bot's GitHub App while 
  the bot is running.
"""
def obtain_installations(git_integration):
    # Get the list of installations of the bot's GitHub App
    installations = git_integration.get_installations()

    repositories_info = []

    # Obtain details about each installation
    for installation in installations:
        # Obtain the ID of each installation of the GitHub App
        installation_id = installation.id
        # Obtain the repositories where the bot is installed
        repositories = installation.get_repos()
        for repository in repositories:
            """
            Create a list containing the repositories where the bot is installed, the owners of the repositories, and the
            ID of each of the installations of the GitHub App.
            """
            repositories_info.append((repository.name, repository.owner.login, installation_id))

    return repositories_info


"""
* For each repository that has the bot's GitHub App is installed:
    + This function obtains the latest version of the Bot/config.json file either from the repository if it is available, 
      or from the local directory, otherwise. 
    + If emails for lingering issues are enabled in config.json (by having the "send-emails" field set to true and the 
      "when-to-send" field set to "lingering" or "all"), then the function collects all the issues in the repository 
      that are currently open, checks either their creation date, or their last modified date (depending on the value of
      the "lingering_mode" field set in config.json: "creation-date"/"last-modified"), and determines whether they are 
      lingering or not, depending on the value of the "lingering-issue-threshold"" field set in config.json, which 
      specifies the number of days (the threshold) after an issue would be considered lingering. 
    + The issues that are found to be lingering are the ones that practitioners will be notified about, by sending them 
      emails.
"""
def process_lingering_issues(git_integration, lingering_check_frequency):

    repositories_info = obtain_installations(git_integration)

    # Iterate over each repository that has the bot's GitHub App installed
    for repository_name, repository_owner, installation_id in repositories_info:
        print(f"Processing lingering issues in the {repository_name} repository...", flush=True)

        # Get a git connection as our bot
        git_connection = Github(login_or_token=git_integration.get_access_token(installation_id).token)

        repo = git_connection.get_repo(f"{repository_owner}/{repository_name}")
        # If repo has config.json file in the Bot directory, use it. Otherwise, use the config.json file locally in the bot
        try:
            config_file = repo.get_contents("Bot/config.json")
            print("Using config file from the repository", flush=True)
            # Decode the file
            config = json.loads(base64.b64decode(config_file.content).decode("utf-8"))
        except:
            with open("config.json", "r") as f:
                config = json.load(f)
                print("Using config file from the local Bot directory as it is not present in the repository", flush=True)

        # Send email if emails for lingering issues/all types of emails are enabled in config.json
        if config["send-emails"] == True and config["when-to-send"] in ["lingering", "all"]:
            print("Sending emails for lingering issues enabled", flush=True)
            # Obtain all open issues in the current repository
            issues = repo.get_issues(state="open")
            email_info = config["email-info"]
            lingering_issue_threshold = email_info["lingering-issue-threshold"]
            lingering_mode = email_info["lingering-mode"]
            # Determine the appropriate function to get the issue time based on lingering_mode
            if lingering_mode == "last-modified":
                get_issue_time = lambda issue: issue_last_modified(issue)
            elif lingering_mode == "creation-date":
                get_issue_time = lambda issue: issue.created_at
            else:
                """
                Lingering mode is neither "last-modified", nor "creation-date", so we return early and we don't check 
                for lingering issues anymore.
                """
                print(f"Lingering mode: {lingering_mode} is not a valid mode, please refer to the bot documentation.",
                      flush=True)
                return
            print(f"Using lingering mode: {lingering_mode}", flush=True)
            # Obtain the current time and make it timezone-aware in UTC
            current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
            lingering_issues = []
            # Iterate through all open issues in the current repository
            for issue in issues:
                issue_time = get_issue_time(issue)
                # Calculate how many days have passed since the issue has been created/has been last modified
                days_passed = (current_time - issue_time).days
                """
                If the issue has been created/has not been modified for more days than the given threshold, add it to 
                the list of lingering issues.
                """
                if days_passed >= lingering_issue_threshold:
                    # Add lingering issue to the lingering_issues list
                    lingering_issues.append(issue)
            print(f"Found {len(lingering_issues)} lingering issue(s)", flush=True)
            # Send email for lingering issues, if any
            if len(lingering_issues) > 0:
                print("Sending email...", flush=True)
                send_email(lingering_issues, config, 1)
        else:
            print(f"Sending emails for lingering issues disabled, checking again in {lingering_check_frequency} day(s)",
                  flush=True)