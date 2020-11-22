""" - AnkiFish v1.0 -
This program takes a list of words and creates a csv file from
which flashcards containing a translation to another language,
an example sentence, picture and audio can be imported into the
flashcard learning program ANKI.

Languages currently supported:
- Spanish
- French
- Italian

Written by Philipp Spengler and Fabian Bubla (May, 2018)

*
Compatible with Windows 10 and MacOSX
*

"""
try:
    import sys
    import tkinter as tk
    from tkinter import messagebox
    from tkinter import filedialog
    from google_images_download import google_images_download
    from os.path import basename
    import os
    from os import getcwd
    import requests, bs4, selenium
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    import csv
    from getpass import getuser
    import urllib
except ModuleNotFoundError as error:
    # if any modules are not yet installed, AnkiFish will show an error message and request the user to install them
    print("It looks like your missing some modules - " + error.__class__.__name__)
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", "It looks like you are missing some modules - " + str(error) + "\n \n Please install the missing modules.")
    root.destroy()
    sys.exit() 

# ----------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------
#[Philipp]
# this class contains the entire application
class App(tk.Tk):
    
    def __init__(self):
        tk.Tk.__init__(self)
        self.filename = "" # contains the file location
        self.words = [] # contains all words to be translated
        self.translate_to = tk.StringVar() # contains the language code for translation
        self.include_sentence = tk.IntVar() # does the user want example sentences - boolean (1 -> True/0 -> False)
        self.include_image = tk.IntVar() # does the user want pictures - boolean(1 -> True/0 -> False)
        self.include_audio = tk.IntVar() # does the user want audio files - booelan(1 -> True/0 -> False)
        # Window styling
        self.title("AnkiFish v1.0")
        self.wm_iconbitmap('Logo.ico')
        # AnkiFish Logo (top right corner)
        logo = tk.PhotoImage(file="Logo.gif")
        tk.Label(self,
                 image=logo
                 ).grid(row=1, column = 3, sticky="w")

        # button for creating a new file
        tk.Button(self,
          text = "New File",
          width = 15,
          command = self.create_new_file,
          ).grid(row = 1, column = 0, sticky="swe") 
        # button for opening an existing file
        tk.Button(self,
          text = "Open Existing File",
          width = 15,
          command = self.open_file,
          ).grid(row = 1, column = 1, sticky="swe")

        # Banner that displays the file that will be saved
        self.filebanner = tk.Text(self, height = 1)
        self.filebanner.grid(row = 2, column = 0, columnspan = 2, sticky="we")

# ----------------------------------------------------------------------------------

        # Entry field for words to make flashcards from
        tk.Label(self,
                 text = "Enter a word:",
                 wraplength = 80
                 ).grid(row = 3, column = 0)
        self.entry_word = tk.Entry(self)
        self.entry_word.grid( row = 4, column = 0, sticky ="e")
        self.entry_word.bind("<Return>", (lambda event: self.submitword())) # allows submitting a word with the 'enter' key
        # Submit button
        tk.Button(self,
                  text = "Submit",
                  command = self.submitword
                  ).grid(row = 4, column = 1, sticky="w")
        self.words_label = tk.Label(self)
        self.words_label.grid( row = 5)
# ----------------------------------------------------------------------------------       
        # Extra Options

        # Choose which language to translate to
        tk.Label(self,
                 text = "Translate to:"
                 ).grid( row = 6, column = 0)
        languages = {"Spanish":"es", "French":"fr", "Italian":"it"}
        self.translate_to.set("es")
        for key, value in languages.items():
            tk.Radiobutton(self,
                           text = key,
                           value = value,
                           variable = self.translate_to
                           ).grid(column = 0)
                           
        # Include Pictures, Audio, Example Sentence?
        tk.Label(self,
                 text = "Include:"
                 ).grid( row = 6, column = 1)
        tk.Checkbutton(self,
                       text = "Example Sentence",
                       variable = self.include_sentence
                       ).grid(row = 7, column = 1)
        tk.Checkbutton(self,
                       text = "Picture",
                       variable = self.include_image
                       ).grid(row = 8, column = 1)
        tk.Checkbutton(self,
                       text = "Audio",
                       variable = self.include_audio
                       ).grid(row = 9, column = 1)
# ----------------------------------------------------------------------------------                

        # Run the program
        tk.Button(self,
                  text = "Run",
                  width = 15,
                  command = self.run
                  ).grid(column = 0, row = 11)

        # Banner that informs the user about the current state of the program.
        self.banner = tk.Label(self,
                               text = "",
                               anchor = "w",
                               justify = "left",
                               wraplength = 250)
        self.banner.grid(column = 0, sticky ="w")
        
        self.mainloop()

# ---------------------------------------------------------------------------------- 
    # methods called by tkinter buttons
    
    def create_new_file(self):
        """function is called when creating a new file - will warn the user if the file already exists"""
        self.filename = filedialog.asksaveasfilename(filetypes=[("CSV","*.csv")], defaultextension =".csv") 
        self.filebanner.delete(1.0, "end")
        self.filebanner.insert("end", self.filename) # updates the banner that displays the filename
        print( self.filename)
    def open_file(self):
        """function is called when opening an existing file"""
        self.filename = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        self.filebanner.delete(1.0, "end")
        self.filebanner.insert("end", self.filename) # updates the banner that displays the filename
        print( self.filename)
    def submitword(self):
        """function is called when submitting a word (button/enter key)"""
        self.words.append( self.entry_word.get()) # adds the word to the list of words to be translated
        self.words_label.config( text = "\n".join(self.words)) # displays the added word in tkinter
        self.entry_word.delete(0, 'end') # clears the entry field
#[Fabian]
    def write_csv(self):
        """function is called when all information about words is gathered - writes everything into the csv file"""
        print( "Starting write_csv")
        csv_file_obj = open(self.filename, 'a+', newline='', encoding='utf-8')
        csv_writer = csv.writer(csv_file_obj) 
        for wordobject in self.words:
            csvlist = [] # for each word in the wordlist, the list which will be written to the csv file is emptied - this ensures every word gets its own line in the csv file
            try:
                # if any of the attributes does not exist at all (e.g. when a word is skipped because there is no translation), skip to the next word the user entered.
                # adds all the attributes of one word to the csvlist
                csvlist.append(wordobject.word)
                csvlist.append(wordobject.translation)
                csvlist.append(wordobject.sentence)
                csvlist.append(wordobject.picture)
                csvlist.append(wordobject.audio)
            except:
                continue
            csv_writer.writerow(csvlist) # writes the contents of csvlist to one row in the csvfile                    
        csv_file_obj.close()
        print( "CSV written.")
# ----------------------------------------------------------------------------------
#[Philipp & Fabian]
    # Run function
    def run(self):
        """runs the main program"""
        def isInternet(host='http://google.com'):
            try:
                urllib.request.urlopen(host)
                return True
            except:
                return False
#[Philipp]
        def updatebanner(updatetext):
            """ updates the information banner in the program window """
            self.banner.config( text = updatetext)
            self.banner.update_idletasks()

        # makes sure the user has chosen a file to write to    
        if self.filename == "":
            updatebanner("Oops! It looks like you haven't chosen a file to write to yet.")
            return
        # makes sure the user is connected to the internet
        if not isInternet():
            updatebanner("Oops! It looks like you're not connected to the internet.")
            return

        # counts the amount of errors encountered when looking for example sentences and pictures and documents where they occurred.
        no_of_errors = 0
        errors = { "senterror": [], "picerror":[]}

        # informs the user that the program has started successfully
        updatebanner("Running...")

        # iterates through all words specified by the user
        for i in range(len(self.words)):
            wordobject = Word(self.words[i], self.translate_to.get()) # creates an object of the class word
            try:
                # gets the translation of the word
                wordobject.getTranslation()
            except selenium.common.exceptions.NoSuchElementException:
                # long gibberish words produce this error and are skipped
                print( "No such word exists. Word will be skipped.")
                continue

            if self.include_sentence.get() == 1: # if the user chose to include example sentences
                try:
                    # gets the example sentence from google translate
                    wordobject.getSentence()
                except:
                    # error is produced when no example sentence exists for this word
                    errors["senterror"].append(wordobject.word)
                    no_of_errors += 1
            if self.include_audio.get() == 1: # if the user chose to include audio
                # gets the audio from google translate
                wordobject.getAudio()
            if self.include_image.get() == 1: # if the user chose to inlude images
                try:
                    # gets the picture from google images
                    wordobject.getPicture()
                except:
                    # error is produced when google images returns no results for this word
                    errors["picerror"].append(wordobject.word)
                    no_of_errors += 1
    
            self.words[i] = wordobject # replaces the word string in the wordlist for the complete word object
        
        self.write_csv() # writes all the word objects to the csv file

        # Output in tkinter window
        if no_of_errors > 0:
            # shows for which words no examples or pictures were found
            outputtext = "Finished with errors: \n"
            if errors["senterror"]:
                outputtext += "No example sentence found for " + ", ".join(errors["senterror"]) + "\n"
            if errors["picerror"]:
                outputtext += "No picture found for " + ", ".join(errors["picerror"])
            updatebanner( outputtext)
        else:
            # No errors
            updatebanner( "Finished.")
    
                
        
# ----------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------- 
    
class Word:
    def __init__(self, word, translate_to):
        self.translate_to = translate_to # receives the language code from the main app
        self.word = word # receives the word to translate from the main app
        self.translation = "" # translation(s) of the word go in here
        self.sentence = "" # example sentence goes in here
        self.audio = "" # filename of audio goes in here
        self.picture = "" # filename of picture goes in here

# ----------------------------------------------------------------------------------
    # class methods
#[Fabian]    
    def getTranslation(self):
        """ gets a translation for a given word from google translate - if there are adjectives, nouns, and verbs, the functions will return the most common of each"""
        print( "Start getTranslation")
        # opens a browser in the background
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080") #browser resolution, window_size
        
        self.URL= 'https://translate.google.com/#en/' + self.translate_to + '/' + self.word # url of google translation

        if os.name == 'posix': # checks if OS is Mac or Windows
            browser = webdriver.Chrome(chrome_options=chrome_options, executable_path= getcwd() + '/chromedriver')
        else:
            browser = webdriver.Chrome(chrome_options=chrome_options, executable_path= getcwd() + '\\chromedriver.exe')

        browser.get(self.URL)
        html_file= browser.page_source
        soup = bs4.BeautifulSoup(html_file, 'lxml')
        print( "Browser opened")
        data = [] # this list wil contain the raw data from google translate
        translationlist=[] # this list will contain the possible translations of the given word

        # downloads the table of translations and iterates throught them to append them to a list
        for tr in browser.find_elements_by_xpath('//*[@id="gt-lc"]/div[2]/div[2]/div/div/div[2]/table/tbody'):
            tds = tr.find_elements_by_tag_name('td')
            if tds:
                data.append([td.text for td in tds])
        print( "Data retrieved")
#[Philipp]        
        def cleanlist(dirtylist):
            """ cleans the obtained list by removing empty strings and formats everything in one list """
            d = dirtylist.pop() # returns only the inner list
            return [value for value in d if value != ""] # returns new list without empty strings
        self.sentencer = "" # variable will contain only the first word of the translation for looking up an example sentence
#[Fabian]
        try:
            data= cleanlist(data) # cleans up the raw data from google translate
            print( "List cleaned")
            # goes through the obtained data and determines whether a word is a noun, adjective, or verb.
            #Then adds exactly one of each to a list of translations.
            for idx,val in enumerate(data):
                if val == 'noun':
                    translationlist.append(data[idx+1]+ ' ' + data[idx+2] + ' (n)')
                    if self.sentencer == "":
                        self.sentencer += data[idx+2]
                elif val == 'verb':
                    translationlist.append(data[idx+1] + ' (v)')
                    if self.sentencer == "":
                        self.sentencer += data[idx+1]
                elif val == 'adjective':
                    translationlist.append(data[idx+1] + ' (a)')
                    if self.sentencer == "":
                        self.sentencer += data[idx+1]
        except:
            print( "Except statement!")
            #if there is no translation table on google translat, but only a result (usually not as reliable as the table), then the result is used
            strangeword = browser.find_element_by_css_selector('#result_box > span').text
            translationlist.append(strangeword)
            self.sentencer += strangeword
        
                
        print( translationlist)
        print( "Words collected.")
        # joins all possible translations into one string
        self.translation = "\n".join(translationlist)
        print( self.translation)
        print( "Finished")                        
        browser.close()        

    def getSentence(self):
        """ this functions gets an example sentence using the translation from getTranslation()"""
        print( "Start getSentence")
        # opens chrome browser in background
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        # uses the old URL from getTranslation but switches the language codes and adds the translated word-> this is necessary for google translate to come up with example sentences
        new_URL= self.URL[0:30]+self.URL[33:36]+self.URL[30:33]+self.sentencer

        if os.name == 'posix': # checks if OS is Mac or Windows
            browser = webdriver.Chrome(chrome_options=chrome_options, executable_path= getcwd() + '/chromedriver') 
        else:
            browser = webdriver.Chrome(chrome_options=chrome_options, executable_path= getcwd() + '\\chromedriver.exe')
        browser.get(new_URL)
        html_file= browser.page_source
        soup = bs4.BeautifulSoup(html_file, 'lxml')
        print( "Browser started.")
        try:
            self.sentence= '"' + browser.find_element_by_class_name('gt-def-example').text + '"'
        except:
            # raises an error to inform the main program that no example sentence was found
            raise
        print(self.sentence)
        browser.close()
#[Philipp]
    def getAudio(self):
        """ gets the audio for the given word from google translate """
        print( "Running getAudio")
        foldername = 'fishmedias'
#[Fabian]
        if os.name=='posix':
            mediapath = '/Users/'+ getpass.getuser()+'/Library/Application Support/Anki2/User 1/collection.media/' + foldername
        else:
            mediapath = 'C:\\Users\\' + os.getlogin() + '\\AppData\\Roaming\\Anki2\\User 1\\collection.media\\' + foldername
#[Philipp]
        if not os.path.exists(mediapath): # checks if AnkiFish has already created its own folder in the anki media collection
            os.makedirs(mediapath)
        splitstring = self.translation.split()
        print(' this is the split string:' + str(splitstring))
        # cleans up the translation so that google translate only pronounces the words (i.e. not n or a for nouns and adjectives)
        for i in range(len(splitstring)):
            if "(" in splitstring[i]:
                       splitstring[i] = ","
        audiotranslation = " ".join([x for x in splitstring if "\n" not in x])
#[Fabian]
        url='https://translate.google.com.vn/translate_tts?ie=UTF-8&q=' + audiotranslation + '&tl=' + self.translate_to + '&client=tw-ob' # direct url to audio file
        res= requests.get(url)
        try:
            res.raise_for_status()
            if os.name=='posix': # checks if OS is Mac or Windows then creates mp3 file according to the right path
                audioFile = open(mediapath + '/' + audiotranslation + '.mp3', 'wb+') 
                print (mediapath + '/'+ audiotranslation)
            else:
                audioFile = open(mediapath + '\\' + audiotranslation + '.mp3', 'wb+')
                print (mediapath + '\\'+ audiotranslation)

            print( "Audio received, saving")
            # writes the audio to an .mp3 file
            for chunk in res.iter_content(100000):
                audioFile.write(chunk)
            audioFile.close()

            if os.name=='posix': # checks if OS is Mac or Windows
                self.audio = "[sound:" + foldername + "/" + audiotranslation + ".mp3]"
            else:
                self.audio = "[sound:" + foldername + "\\" + audiotranslation + ".mp3]"
            print( "Finished.")
        except HTTPError:
            print('Sorry there was no audio')
#[Philipp]
    def getPicture(self):
        """ gets a picture associated with the word """
        foldername = 'fishmedias'
        if os.name=='posix': # checks if OS is Mac or Windows and sets correct path
            mediapath = '/Users/'+ getpass.getuser()+'/Library/Application Support/Anki2/User 1/collection.media/' + foldername
        else:
            mediapath = 'C:\\Users\\' + os.getlogin() + '\\AppData\\Roaming\\Anki2\\User 1\\collection.media\\' + foldername

        if not os.path.exists(mediapath): # checks if AnkiFish has already created its own folder in the anki media collection
            os.makedirs(mediapath)
        word = self.word

        response = google_images_download.googleimagesdownload()
        # specifies format, aspect ratio, output directory, and to exclude NSFW pictures from image search
        arguments = {'keywords': word,
                     'prefix': word,
                     'limit': 1,
                     'format': 'jpg',
                     'aspect_ratio': 'square',
                     'print_paths': True,
                     'no_directory': True,
                     'safe_search': True,
                     'output_directory': mediapath + foldername}
        paths = response.download(arguments) # downloads picture from google images
        picname = basename( "".join(paths[word]))
        if picname != "":
            self.picture = foldername + "\\" + picname
        else:
            # raises an error to inform the main program that no picture was found
            raise

# ----------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------

if __name__ == '__main__':
    # starts the program upon executing the .py file
    App()


