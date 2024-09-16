import json
import random
from typing import Any
from openai import OpenAI
import os
from instructor.batch import BatchJob
from instructor import from_openai

from pydantic_models.article_corpus_model import ArticleCorpus


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
        self.client = from_openai(OpenAI())

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

        articles = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            response_model=ArticleCorpus,
            # tools=[openai.pydantic_function_tool(ArticleGenerationPrompt)],
        )

        return articles

    def save_generated_articles(self, articles: ArticleCorpus):
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

        # Save generated articles to JSON file
        self.save_generated_articles(response)

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

    def create_message_generator(self, n: int, custom_id_prefix: str = "request"):
        """
        Creates a generator of the messages to be used with instructor's BatchJob which then sends the batch request to the OpenAI API.
        """

        for i in range(0, n):
            random_articles: list[dict] = self.choose_random_articles()
            prompt = self.create_openai_prompt(random_articles)

            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ]

            yield messages

    def create_batch_json(self, message_generator, batch_jsonl_path: str):
        """
        Sends a batch request to the OpenAI API with the prompts in the batch file.
        """

        BatchJob.create_from_messages(
            messages_batch=message_generator,
            model=self.model_name,
            file_path=batch_jsonl_path,
            response_model=ArticleCorpus,
        )

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

        parsed, unparsed = BatchJob.parse_from_file(
            file_path=batch_response_path, response_model=ArticleCorpus
        )
        for i, article in enumerate(parsed):
            self.save_generated_articles(article)
            print(f"Generated responses: {i+1} out of {len(parsed)} saved.")

        # return parsed, unparsed

        # with open(batch_response_path, "r") as f:
        #     responses = f.readlines()

        # responses = [json.loads(response) for response in responses]

        # return responses
