from article_generator import ArticleGenerator


def run_article_generator():

    # Name of the GPT model to use
    model_name = "gpt-4o-mini"

    # Temperature parameter for the GPT model
    temperature = 0.0

    # Path to the JSON file containing the articles
    article_json_path = "found_articles.json"

    # Path to the JSON file where the generated articles should be saved
    article_output_path = "generated_articles.json"

    # Batch file path
    batch_file_path = "batch_file.jsonl"

    # Batch response path
    batch_response_path = "data/created_articles/batch_data/batch_a.jsonl"

    # The prefix for the custom ID of the generated articles
    custom_id_prefix = "b - request"

    # Number of articles to choose from the JSON file (amount used for few shot prompting)
    num_articles_to_choose = 3

    # Number of times to generate using the GPT model
    times_to_generate = 1_000

    # Initialize the ArticleGenerator class
    article_generator = ArticleGenerator(
        article_json_path=article_json_path,
        article_output_path=article_output_path,
        num_articles_to_choose=num_articles_to_choose,
        model_name=model_name,
        temperature=temperature,
    )

    # article_generator.create_batch_file(
    #     n=times_to_generate,
    #     batch_file_path=batch_file_path,
    #     custom_id_prefix=custom_id_prefix,
    # )
    # article_generator.generate_batch(batch_file_path=batch_file_path)

    article_generator.read_batch_response_jsonl(batch_response_path=batch_response_path)


if __name__ == "__main__":
    run_article_generator()
