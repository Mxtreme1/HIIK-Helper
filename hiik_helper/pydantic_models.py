from pydantic import BaseModel, Field


class ArticleGenerationPrompt(BaseModel):
    class Article(BaseModel):
        Headline: str = Field(description="Headline of the article")
        Subheadline: str = Field(description="Subheadline of the article")
        Paragraphs: str = Field(description="Paragraphs of the article")

    articles: list[Article]
