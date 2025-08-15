import os
import sys
import django
from django.utils.text import slugify
from django.contrib.auth import get_user_model

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from cms.models import Article, Category, ArticleCategory
from tenants.models import Tenant

def run():
    """
    Creates 12 articles for each of the first 4 categories of tenant with ID 1.
    """
    try:
        # Get tenant with ID 1
        tenant = Tenant.objects.get(id=1)
        print(f"Found tenant: {tenant.name}")

        # Get the first user of the tenant to be the author
        author = get_user_model().objects.filter(tenant=tenant).first()
        if not author:
            print(f"No users found for tenant: {tenant.name}")
            return

        print(f"Using author: {author.username}")

        # Get the first 4 categories for the tenant
        categories = Category.objects.filter(tenant=tenant)[:4]
        if not categories:
            print(f"No categories found for tenant: {tenant.name}")
            return

        print(f"Found {len(categories)} categories.")

        # Loop through each category and create 12 articles
        for category in categories:
            print(f"Creating 12 articles for category: {category.name}")
            for i in range(1, 13):
                title = f"{category.name} - Article {i}"
                slug = f"category-{category.id}-article-{i}"
                content = f"This is the content for article {i} in category {category.name}."

                # Create the article
                article = Article.objects.create(
                    title=title,
                    slug=slug,
                    content=content,
                    author=author,
                    tenant=tenant,
                    status='published',
                )

                # Associate the article with the category
                ArticleCategory.objects.create(
                    article=article,
                    category=category,
                    tenant=tenant
                )

                print(f"  - Created article: {title}")

        print("\nScript finished successfully!")

    except Tenant.DoesNotExist:
        print("Tenant with ID 1 not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    run()
