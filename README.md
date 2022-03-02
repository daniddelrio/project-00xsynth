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
    - _id: ObjectID
    - keyword: String
    - account_id: String
    - username: String
    - has_been_scraped: Boolean (default: False, determines whether to scrape ALL following)
    - keyword_id: ObjectID (reference to input_keyword)
    - timestamp: Date (required)
    
`watchlist`
    - _id: ObjectID
    - account_id: String (indexed)
    - timestamp: Date (order by timestamp)

`discord_link`
    - _id: ObjectID
    - account_id: String (indexed)
    - url: String (indexed)
    - joined: Boolean (default: false)
    - verified: Boolean (default: false)
    - valid: Boolean (default: true)
    - created_at: Date
