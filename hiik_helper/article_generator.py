import json
import random
from openai import OpenAI
import os

from pydantic_models import ArticleGenerationPrompt


class ArticleGenerator:
    def __init__(
        self,
        article_json_path: str = "found_articles.json",
        article_output_path: str = "generated_articles.json",
        num_articles_to_choose: int = 3,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0,
    ):
        """
        Uses a GPT model to generate more articles based on the articles given in the JSON file under the path article_json_path.
        This is done by using few shot prompting after choosing multiple random articles from the JSON file.

        Args:
        article_json_path: str
            Path to the JSON file containing the articles
        article_output_path: str
            Path to the JSON file where the generated articles should be saved
        batch_file_path: str
            Path to the JSON line file of the prompts to be used with OpenAI's batch API
        num_articles_to_choose: int
            Number of articles to choose from the JSON file (amount used for few shot prompting)
        times_to_generate: int
            Number of times to generate using the GPT model
        model_name: str
            Name of the GPT model to use
        temperature: float
            Temperature parameter for the GPT model

        """

        self.article_output_path: str = article_output_path
        self.num_articles_to_choose: int = num_articles_to_choose
        self.model_name: str = model_name
        self.temperature: float = temperature

        with open(article_json_path, "r") as f:
            self.articles: dict = json.load(f)

        # Reads the API key from the environment variable
        # export OPENAI_API_KEY="your_api_key_here"
        self.client = OpenAI()

        self.system_prompt: str = (
            """
            You are a journalist for a reputable local news organization covering international conflicts. 
            You are given old articles from yourself and based on these articles are to write new articles on different events that could happen in the same conflict in the same style. 
            Do not rewrite the old articles, but use them as inspiration for new articles."""
        )

    def choose_random_articles(self) -> list[dict]:
        """
        Chooses random articles from the JSON file according to the num_articles_to_choose parameter.

        Returns:
        list[dict]
            List of randomly chosen articles from the JSON file
        """

        random_articles: list = random.sample(
            list(self.articles.keys()), self.num_articles_to_choose
        )

        random_articles = [self.articles[article] for article in random_articles]

        return random_articles

    def create_openai_prompt(self, random_articles: list[dict]) -> str:
        """
        Creates a few shot prompt for the GPT model based on the random articles chosen.

        Args:
        random_articles: list[dict]
            List of randomly chosen articles from the JSON file

        Returns:
        str
            Few shot prompt for the GPT model
        """
        prompt = ""

        # Only add the headline, subheadline and paragraphs to the prompt as the rest is extracted from the web page when analyzing unseen articles
        for article in random_articles:
            prompt += f"Headline: {article['headline']}\n"
            prompt += f"Subheadline: {article['subheadline']}\n"

            # Remove lorem ipsum from paragraphs
            article["paragraphs"] = article["paragraphs"].replace(
                "\nLorem ipsum dolor sit amet, consectetur.", ""
            )
            prompt += f"Paragraphs: {article['paragraphs']}\n"

        return prompt

    def send_openai_request(self, prompt: str):
        """
        Send a request to the OpenAI API with the few shot prompting, and return the generated article.
        Uses the API key, model name and temperature parameters provided in the constructor.
        Further uses the pydantic model ArticleGenerationPrompt to validate the response.
        """

        articles = self.client.beta.chat.completions.parse(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            response_format=ArticleGenerationPrompt,
            # tools=[openai.pydantic_function_tool(ArticleGenerationPrompt)],
        )

        return articles

    def save_generated_articles(self, articles: ArticleGenerationPrompt):
        """
        Save the generated articles to the JSON file under the path article_output_path.
        If the file does not exist, it should be created.

        Args:
        articles: ArticleGenerationPrompt
            The generated articles to save in the pydanctic model format
        """
        # Bring the articles into a dictionary format

        article_list = []
        for article in articles.articles:
            headline = article.Headline
            subheadline = article.Subheadline
            paragraphs = article.Paragraphs
            article_list.append(
                {
                    "headline": headline,
                    "subheadline": subheadline,
                    "paragraphs": paragraphs,
                }
            )

        # Check if the file exists and create it if it does not
        if not os.path.exists(self.article_output_path):
            with open(self.article_output_path, "w") as f:
                json.dump([], f)  # Create an empty JSON file

        # Append the generated articles to the JSON file
        with open(self.article_output_path, "r") as f:
            data = json.load(f)
        with open(self.article_output_path, "w") as f:
            data += article_list
            json.dump(data, f)

    def generate_once(self):
        # Sample random articles
        random_articles: list[dict] = self.choose_random_articles()

        # Connect to OpenAI API and generate articles
        prompt = self.create_openai_prompt(random_articles)
        response = self.send_openai_request(prompt)

        # Extract the articles from the response
        articles = response.choices[
            0
        ].message.parsed  # Received articles as pydantic model (see pydantic_models.py)

        # Save generated articles to JSON file
        self.save_generated_articles(articles)

    def generate(self, n: int):
        """
        Randomly samples articles from the JSON file and uses them for few shot prompting with the GPT model.
        This is repeated times_to_generate times.

        The input news articles are in a JSON file with the following structure:
            "$URL": {
            "url": "$URL",
            "accessing-date": "$UTC_DATETIME_ACCESS",  # like "2024-08-25 12:34:14.660861+00:00"
            "last-modification": "$UTC_DATETIME_MODIFICATION",  # like "2024-08-23T15:42:14+00:00"
            "headline": "$HEADLINE",
            "subheadline": "$SUBHEADLINE",
            "paragraphs": "$PARAGRAPHS"
            }

        Although the articles are in the JSON file, the GPT model will not have access to the URL, accessing-date and last-modification fields.
        The GPT model will only have access to the headline, subheadline and paragraphs fields.

        The output from GPT is a Pydantic model with the following structure:
            class ArticleGenerationPrompt(BaseModel):
                class Article(BaseModel):
                    Headline: str = Field(description="Headline of the article")
                    Subheadline: str = Field(description="Subheadline of the article")
                    Paragraphs: str = Field(description="Paragraphs of the article")
                articles: list[Article]

        The generated articles are appended to a JSON file with the same structure, if it does not exist it should be created.

        Args:
        n: int
            Number of times to generate using the GPT model
        """
        for i in range(0, n):
            self.generate_once()
            print(
                f"Generated articles: {i+1} out of {n} with {self.num_articles_to_choose} chosen each. Sum of articles generated: {self.num_articles_to_choose*(i+1)}"
            )

        print(
            f"{n} times generated and saved successfully under {self.article_output_path}."
        )

    def create_batch_file(
        self,
        n: int,
        batch_file_path: str = "batch_file.jsonl",
        custom_id_prefix: str = "request",
    ):
        """
        Creates a json line file of the prompts to be used with OpenAI's batch API.

        Args:
        n: int
            Number of times to generate using the GPT model
        batch_file_path: str
            Path to the JSON line file of the prompts to be used with OpenAI's batch API
        custom_id_prefix: str
            The prefix for the custom ID of the generated articles
        """

        # Check if the file exists and create it if it does overwrite it
        with open(batch_file_path, "w") as f:
            f.write("")

        # Create the batch file
        for i in range(0, n):
            random_articles: list[dict] = self.choose_random_articles()
            prompt = self.create_openai_prompt(random_articles)

            prompt = {
                "custom_id": f"{custom_id_prefix}-{i+1}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": self.model_name,
                    "temperature": self.temperature,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                },
            }

            # Save the prompt to the batch file immediately as it might be too large to store in memory
            with open(batch_file_path, "a") as f:
                f.write(json.dumps(prompt) + "\n")
            print(f"Batch file: {i+1} out of {n} created.")

    def generate_batch(self, batch_file_path: str = "batch_file.jsonl"):
        """
        Sends a batch request to the OpenAI API with the prompts in the batch file.
        The generated articles are saved to the JSON file under the path article_output_path.

        Args:
        batch_file_path: str
            Path to the JSON line file of the prompts to be used with OpenAI's batch API
        """

        batch_input_file = self.client.files.create(
            file=open(batch_file_path, "rb"), purpose="batch"
        )
        print(f"Batch request uploaded successfully.")

        batch_object = self.client.batches.create(
            input_file_id=batch_input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"description": "Batch request for article generation."},
        )

        print(f"Batch request sent successfully.")
        print(batch_object)

    def read_batch_response_jsonl(self, batch_response_path: str):
        """
        Reads the JSON line file with the batch response from the OpenAI API and returns the responses.

        Args:
        batch_response_path: str
            Path to the JSON line file with the batch response from the OpenAI API

        Returns:
        list[ArticleGenerationPrompt]
            List of the generated articles in the pydantic model format
        """

        with open(batch_response_path, "r") as f:
            responses = f.readlines()

        responses = [json.loads(response) for response in responses]

        return responses
