import logging
import random
from playwright.sync_api import sync_playwright, Page
import pandas as pd

url = f"https://doyoutrackid.com/"

output_csv_file = 'output/generated.csv'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler("artist_info.log"),
        logging.StreamHandler()
    ]
)
data_list=[]
logging.info("Scrapping data start successfully")
def scrap_tracks(page: Page, href: str, data_list: list):
    page.wait_for_selector("li[class^='Tracks_listItem']")
    list_items = page.query_selector_all("li[class^='Tracks_listItem']")
    # Iterate through the list items and scrape track information
    for item in list_items:
        title_elem = item.query_selector("[class^='Track_title']")
        title = title_elem.inner_text().strip() if title_elem else "No title"
        artist_elem = item.query_selector("[class^='Track_artist']")
        artist = artist_elem.inner_text().strip() if artist_elem else "No artist"
        album_elem = item.query_selector("[class^='Track_album'] span[class^='Track_value']")
        album_text = album_elem.inner_text().strip() if album_elem else "No album"
        release_date_elem = item.query_selector("p[class^='Track_releaseDate'] span[class^='Track_value']")
        date_text = release_date_elem.inner_text().strip() if release_date_elem else "No release date"
        time_stamp_elem = item.query_selector("p[class^='Track_time']")
        time_stamp = time_stamp_elem.inner_text().strip() if time_stamp_elem else "No timestamp"
        # Log scrapping tracks
        logging.info('Starting data extract...')
        logging.info(f"Title: {title}")
        logging.info(f"Artist: {artist}")
        logging.info(f"Album: {album_text}")
        logging.info(f"Release Date: {date_text}")
        logging.info(f"Timestamp: {time_stamp}")
        logging.info(f"URL: {href}")
        logging.info("-" * 40)
        data_list.append({
            'Title': title,
            'Artist': artist,
            'Album': album_text,
            'Release_Date': date_text,
            'Timestamp': time_stamp,
            'URL': href
        })
    return data_list

def run(page: Page, data_list: list):
    # Go to the URL stored in the variable
    page.goto(url)
    page.locator('a:has-text("Archive")').nth(0).click()
    page.wait_for_selector('li.BananaDates_listItem__SDPAB')
    list_items = page.query_selector_all('li.BananaDates_listItem__SDPAB')
    href_links = []
    for item in list_items:
        # Find the anchor (<a>) tag inside the list item
        link = item.query_selector('a')
        if link:
            href = link.get_attribute('href')
            href_links.append(href)
            logging.info(f'Link: {href}')
        else:
            # If there is no <a> tag inside, print that no link was found
            logging.info('No link found in this list item.')
    latest=href_links[-1:]
    for href in latest:
        full_url = "https://doyoutrackid.com" + href
        logging.info(f'Navigating to: {full_url}')
        page.goto(full_url)  # Navigate to the stored href link
        v=random.randint(3000, 6000)
        page.wait_for_timeout(v)
        logging.info("wait for timeout"+ str(v))
        page.wait_for_selector("li[class^='Tracks_listItem']")      
        tracks=scrap_tracks(page, full_url, data_list)
        logging.info('Starting update genre process...')
        from last_fm_add_genres import enter_genres
        genres=enter_genres(tracks) # Get genres from audioscrobbler
    return genres

def main():
    try:
        with sync_playwright() as playwright:
            logging.info("Launching browser with Playwright.")
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            logging.info("Browser launched successfully.")
            tracks = run(page, data_list)
            df = pd.DataFrame(tracks)
            df.to_csv(output_csv_file, index=False)
            logging.info(f"Scraped a total of {len(tracks)} tracks.")
            logging.info("Data successfully loaded using load_data().")
            browser.close()
            logging.info("Browser closed successfully.")
    except Exception as e:
        logging.critical(f"An unexpected error occurred in the main function: {e}", exc_info=True)

if __name__ == "__main__":
    main()
