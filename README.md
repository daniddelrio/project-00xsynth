# project-00xsynth

Workflow for automation of scraping of Tweets

## Starting and Testing the Functions
Make sure you have Docker installed on your device.

1. Make a file called `.env` containing the filled out variables set in `.env.example`.
2. Open the terminal and `cd` into this directory.
3. Build the images by running `docker-compose build`
4. Run the containers by running `docker-compose up`
5. If you would like to test a specific Lambda function locally, run `curl -XPOST "http://localhost:PORT/2015-03-31/functions/function/invocations" -d '{}'`, and replace `PORT` with the port correspoding to the function you want to run (you can find the port for each function in the `docker-compose.yml` file).

## Deploying Updated Functions/Scripts
1. After updating the code, build the images again with `docker-compose build`.
2. Run `aws ecr get-login-password | docker login --username AWS --password-stdin 357518498432.dkr.ecr.ap-southeast-1.amazonaws.com` to connect to the AWS ECR repositories.
3. Run `docker-compose push` to push the updated images to the ECR repositories.

## Diagram Workflow
![Scraper Flowchart drawio](https://user-images.githubusercontent.com/35568696/156316743-e0048f94-2820-4e5d-8280-43d5491d88b8.png)

## Technologies Used
These are hosted on AWS, and the database is hosted on MongoDB Atlas. All images are hosted on **Elastic Container Registry (ECR)**. These images are then used to deploy to **Lambda functions**, which represent the workflows/scripts. Some Lambda functions are combined to form one workflow using **Step Functions**.

Since we want to run each workflow/script in regular intervals, we use **Amazon EventBridge** to schedule the execution of these workflows every 30 mins (can be adjusted). Logs of all exectuions are then found in **Amazon CloudWatch**. Contact the developer if you want to request for the videos that detail the instructions for running the scripts.

### List of Functions
**add_username**
- This function allows you to add the usernames of accounts that you want to track.
- Requires an `event` object. Sample can be found below:
```
{
  "Username": "addusernamehere"
}
```

**follows_category**
- This function categorizes all the scraped accouunts in the `temp_followed` collection according to if they have a Discord URL in their bios.

**join_discord**
- This function scrapes the `discord_links` collection and attempts to join these servers.

**scrape_follows**
- This function scrapes the accounts that the input accounts follow and adds them to the `temp_followed` collection.

**scrape_liked**
- This function scrapes the accounts of the tweets that the input accounts like and adds them to the `temp_followed` collection.


**tg_send**
- This function consolidates the scraped accounts in `temp_followed` and broadcasts them to the Telegram channel.

**track_watchlist**
- This function checks the watchlist if they've either updated their description with a new Discord bio or they've posted a new tweet that contains a Discord URL.

### Database Schema + Collections
`input`

_Collection of input Twitter accounts that we want to track_

| Field  | Type | Description |
| ------------- | ------------- | ------------- |
| \_id  | ObjectID  | Primary key |
| username  | String  | Username of the twitter account |
| account_id  | String  | ID of the Twitter user |
| timestamp  | Date  | Timestamp when this user was added |
| has_been_scraped  | Boolean  | Boolean for whether the followers of the user have been scraped before |

`watchlist`

_Collection of watchlist (accounts we didn't initially find a Discord link from)

| Field  | Type | Description |
| ------------- | ------------- | ------------- |
| \_id  | ObjectID  | Primary key |
| account_id  | String  | ID of the Twitter user |
| timestamp  | Date  | Timestamp when this user was added |

`discord_link`

_Collection of all discord links found_

| Field  | Type | Description |
| ------------- | ------------- | ------------- |
| \_id  | ObjectID  | Primary key |
| url  | String  | Primary key |
| account_id  | String  | ID of the Twitter user |
| created_at  | Date  | Timestamp when this discord link was added |
| joined  | Boolean  | Whether we've joined this server or not |
| verified  | Boolean  | Whether we've been verified in this server or not |
| valid  | Boolean  | Whether the invite link is valid or not |

`temp_followed`

_Collection where we temporarily store accounts which we'll categorize_

| Field  | Type | Description |
| ------------- | ------------- | ------------- |
| \_id  | ObjectID  | Primary key |
| name  | String  | Name of the account |
| id  | String  | ID of the Twitter user |
| description  | String  | Bio of the user |
| username  | String  | Username of the account |
| type  | String  | Whether we got this account from a follow or a like |
| input  | String  | Username of the source account (i.e. the user we tracked to get this account) |
| created_at  | Date  | Timestamp when this discord link was added |
| entities  | Object  | This contains fields which we need to potentially get the Discord links from |
