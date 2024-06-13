Every morning at 7:30 AM the program does the following

1. Get details about the day's event through Google Calendar API
2. Uses gpt-3 OpenAI API to generate a nice Good morning email
3. Sends that email using Gmail API

This needs Google SERVICE credentials to work and, if using a domain, a domain-wide option enabled for the account.
