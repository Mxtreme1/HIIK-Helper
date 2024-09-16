from pydantic import BaseModel, Field
import json


class ArticleCorpus(BaseModel):
    class Article(BaseModel):
        Headline: str = Field(description="Headline of the article")
        Subheadline: str = Field(description="Subheadline of the article")
        Paragraphs: str = Field(description="Paragraphs of the article")

    articles: list[Article]


def read_json_to_article_generation_prompt(json_path: str) -> ArticleCorpus:
    """
    Read the JSON file containing the articles and return the ArticleGenerationPrompt object containing the articles.
    The headline, subheadline, and paragraphs are required for each article in the JSON file.
    """
    all_articles: ArticleCorpus = ArticleCorpus(articles=[])
    with open(json_path, "r") as file:
        articles = json.load(file)
        for article in articles:
            article_obj = ArticleCorpus.Article(
                Headline=article["headline"],
                Subheadline=article["subheadline"],
                Paragraphs=article["paragraphs"],
            )
            all_articles.articles.append(article_obj)

    return all_articles
