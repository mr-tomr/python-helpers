import requests
from bs4 import BeautifulSoup

def extract_links_from_box(repository_url):
    # Send a GET request to the repository URL
    response = requests.get(repository_url)

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the first box with class "mb-3"
    box = soup.find('div', class_='mb-3')

    # Find all the links within the box
    links = box.find_all('a')

    # Extract the URLs and titles from the links
    link_list = []
    for link in links:
        url = link['href']
        title = link.text
        formatted_link = f"[{title}]({url})"
        link_list.append(formatted_link)

    return link_list

# Replace the following with your desired GitHub repository URL
repository_url = 'https://github.com/mr-tomr/python-helpers/tree/main'

# Call the function to extract links from the box
formatted_links = extract_links_from_box(repository_url)

# Print the formatted links to the screen
print("Formatted Links:")
for link in formatted_links:
    print(link)

# Write the formatted links to a file
file_path = 'formatted_links.txt'
with open(file_path, 'w') as file:
    file.write("Formatted Links:\n")
    for link in formatted_links:
        file.write(link + '\n')

print(f"\nFormatted links have been saved to {file_path}.")
