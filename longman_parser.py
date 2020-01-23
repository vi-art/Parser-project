'''
This Python script is designed to parse vocabulary entries from Longman Dictionary of Contemporary English
(https://www.ldoceonline.com/) according to a user defined WORDLIST_PATH and save it in a text format
suitable for automatic import into Anki - a famous program for creating and studying flashcards.
The script also downloads audio examples from dictionary entries, and integrates them into Anki flashcards,
which makes the process of learning much more efficient.
'''

import re
import codecs
import os.path
import urllib.request, urllib.error
from bs4 import BeautifulSoup

# A path to a text file containing the words that are to be processed by the script. Needs to be created by the user.
# Each new word should be placed on a new line.
WORDLIST_PATH = r'C:\Users\1\Desktop\Wordlist.txt'
# The output file for storing the parsed data. Created automatically.
ANKI_OUTPUT_FILE = r'C:\Users\1\Desktop\Anki_output.txt'
# The folder for storing the downloaded audio files. If it is stored in Anki media folder (the approximate path is
# given below), then there is no need for importing audio, it will be automatically integrated into Anki flashcards
ANKI_MEDIA_FOLDER = r'C:\Users\1\AppData\Roaming\Anki2\Виталий\collection.media\\'

def download(url):
    '''
    Downloads and returns the Longman Dictionary entry's html from the URL address
    of the currently processed word passed from within the main() function
    '''

    response = urllib.request.urlopen(url)
    html = response.read().decode('utf-8')
    return html

def parse(html, output_file):
    '''
    Parses the Longman Dictionary entry for the currently processed word
    passed from within the main() function, writing the entry information
    into the ANKI_OUTPUT_FILE, and storing the downloaded audio files in
    ANKI_MEDIA_FOLDER
    '''

    def get_audio(html):
        '''
        Downloads audio files from the Longman Dictionary entry if present
        '''

        audio_files = re.findall(r'data-src-mp3="(https://d27ucmmhxk51xv.cloudfront.net/media/english/\w+/.+\.mp3)',
                                 str(html))
        print(f'There are {len(audio_files)} audio files: ')

        for audio in audio_files:
            try:
                audiofile_name = re.search(r'([^/]+.mp3)', audio).group(0)
                urllib.request.urlretrieve(audio, ANKI_MEDIA_FOLDER + audiofile_name)
                print('...... downloaded ' + audiofile_name + " audio file.")
            except urllib.error.HTTPError:
                print('...... audio file ' + audio + ' is missing.')
        return audio_files

    def put_sound_tags(html, audio_files):
        '''
        Wraps sound tags around audio files in the original html. This is needed
        for Anki to recognize sound tags and map them to audio files in ANKI_MEDIA_FOLDER
        '''

        for audio in audio_files:
            soundtag = '[sound:' + re.search(r'([^/]+.mp3)', audio).group(0) + ']'
            html = html.replace(audio, soundtag)

        return html

    def del_advertisements(new_html):
        '''
        Removes advertisements from the downloaded dictionary entry
        '''

        ads_removed, count = re.subn(r'(<script.*>(\n|.)+?</script>)', '', new_html)
        if count > 0:
            print(f'Removed {count} ads')
        return ads_removed

    def parse_info(soup_entry, count):
        '''
        Returns a list of basic information about the word
        '''

        word = '<gpskeyword>' + soup.find("h1", attrs={"class": "pagetitle"}).text.strip() + '</gpskeyword>'

        # Find the British pronunciation if given
        try:
            ipa = soup_entry.find("span", attrs={"class": "PRON"}).text.strip()
        except:
            ipa = ''

        # Find the American pronunciation if given
        try:
            ipam = soup_entry.find("span", attrs={"class": "AMEVARPRON"}).text.strip().replace('$', '').lstrip()
        except:
            ipam = ''

        # Find the frequency sign for the core English vocabulary
        try:
            frequency = soup_entry.find("span", attrs={"class": "tooltip LEVEL"}).text.strip()
        except:
            frequency = ''

        # Find the part of speech (noun, verb, adjective, etc.) if given
        try:
            position = soup_entry.find("span", attrs={"class": "POS"}).text.strip()
        except:
            position = ''

        # Find the grammatical category (count/unc noun, tr/intr verb) if given
        try:
            grammar = soup_entry.find("span", attrs={"class": "GRAM"}).text.strip()
        except:
            grammar = ''

        # iid is meant to make sure the entry is unique for Anki database even if the word has a few entries
        iid = word + '_' + str(count)

        info = [iid, word, str(count), ipa, ipam, frequency, position, grammar]
        return info

    def parse_entry(entry, word):
        '''
        Parses the dictionary entry for different meanings
        '''

        content = str(entry).replace("\t", "  ").replace("\n", "").replace("/r", " ")
        content2 = content[0:30] + content[30:].replace('<span class="Sense"', '\r\n<span class="Sense"')
        content3 = content2.replace('<span class="Sense"', '֍<span class="Sense"')

        glosses = content3.split("֍")
        meaning = glosses[1]
        return [meaning, word]


    # Download the audio
    audio_files = get_audio(html)
    print('\n\n\n')

    # Wrap html in sound tags for Anki
    new_html = put_sound_tags(html, audio_files)

    # Remove advertisements
    ads_removed = del_advertisements(str(new_html))

    soup = BeautifulSoup(ads_removed, "html.parser")

    # List all possible dictionary entries for different meanings of the word
    dict_entries = soup.find_all("span", attrs={"class": "dictentry"})

    text = []
    entry_count = 0
    for dict_entry in dict_entries:
        '''
        Parses each dictionary entry for the processed word and inserts Anki tags
        for creating separate flashcards for each meaning of the processed word
        '''

        dictionary_soup = BeautifulSoup(str(dict_entry), "html.parser")
        dict_name = dictionary_soup.find("span", attrs={"class": "dictionary_intro span"})

        # To make sure empty lines and entries from Longman Business Dictionary are excluded.
        if not dict_name or 'From Longman Dictionary of Contemporary English' in str(dict_name):
            soup_entry = BeautifulSoup(str(dict_entry), "html.parser")
            entry_count += 1
            # Get the basic header information about the processed word from the dictionary entry
            header = parse_info(soup_entry, entry_count)

            # Parse different meanings of the processed word
            entries = soup_entry.find_all("span", attrs={"class": "Sense"})

            # Cloze_count is used by Anki to create separate flashcards for each meaning
            cloze_count = 1
            ankified_entries = ''

            for dict_entry in entries:
                ''' 
                Inserts Anki tags to create flashcards inside Anki
                '''

                meaning, word = parse_entry(dict_entry, header[1])
                # Tag the keyword within the definitions so it can be hidden in an Anki flashcard
                word = word.replace("<gpskeyword>", "").replace("</gpskeyword>", "")
                meaning = meaning.replace(word, "<gpskeyword>" + word + "</gpskeyword>")

                if '<span class="DEF">' in meaning:
                    target = re.search(r'<span class="DEF">(.+?)</span>', meaning)
                    meaning = meaning.replace(target.group(0), '{{c' + str(cloze_count) + '::' + target.group(0) + '}}')
                    cloze_count += 1

                ankified_entries += meaning

            final_anki = '\t'.join([ankified_entries] + [''] + header)
            text.append(final_anki)
            print('...... The dictionary entry has been processed')
            output_file.write(final_anki + '\n')

        else:
            print('Ignored dictionary ', dict_name)

def main():
    '''
    Loads the target words from WORDLIST_PATH and runs the script
    '''

    wordlist = codecs.open(WORDLIST_PATH, 'r', encoding='utf-8')
    output_file = codecs.open(ANKI_OUTPUT_FILE, 'w', encoding='utf-8')

    for word in wordlist:
        url = "https://www.ldoceonline.com/dictionary/" + word
        html = download(url)
        parse(html, output_file)

    output_file.close()
    print(f'\nDone. You can now import flashcards from your {os.path.basename(ANKI_OUTPUT_FILE)} file.')

main()
