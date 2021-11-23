from flask import render_template,Blueprint,request,Response,flash,redirect,url_for
from flask.globals import session
from sqlalchemy.sql.elements import or_
from werkzeug.utils import secure_filename
from Whatsapp.models import History ,Content , Attachment
from Whatsapp import db
import os
import csv
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import urllib.parse
from Whatsapp.config import CHROME_PROFILE_PATH
from Whatsapp.config import UPLOAD_FOLDER
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import pyperclip
import psycopg2
import psycopg2.extras
import io
import xlwt
import time






main=Blueprint('main', __name__)

# Front Page
@main.route('/')
def index(): 
    return render_template('front.html')


#Upload file into the database having table History

def allowed_file_extension(filename):
    '''
    This function will check the file extension of the document
    This application only allows xlsx , csv , docx and pdf 
    '''
    file_extension= set(['csv'])
    return '.' in filename and filename.rsplit('.',1)[1].lower() in file_extension

@main.route('/upload',methods = ["POST"])
def upload():
    file1=request.files['fileupload']
    #print(file1)
    
    filetype=file1.mimetype
    if not file1:
        return "No file uploaded"
    if file1 and allowed_file_extension(file1.filename):   
        filename=secure_filename(file1.filename)
        upload=History(file=file1.read().decode('utf-8'),file_extension=filetype,file_name=filename)
        db.session.add(upload)   

        db.session.commit()   
    
        flash("Uploaded!!")
    else:
        flash("Only CSV files allowed")
        return redirect(url_for('main.index'))
    return redirect(url_for('main.mapping') )   #redirect to the mapping function


# Show the Uploaded files 
           
@main.route('/mapping')
def mapping():
    history=History.query.all()

    return render_template('mapping.html',historyData=history)    

@main.route('/back_attachment')
def back_attachment():
    return render_template ('attachment.html')    



@main.route('/main/<int:file_id>/next')
def next(file_id):
    '''
    This next  function will fetch the data from the table (History) and process the data so that it will store into the table Content

    '''    
    file_id=History.query.get_or_404(file_id)

    data=file_id.file.encode('utf-8')
    data1=data.decode('utf-8-sig') #converting byte code into String
    dataSpliting=data1.split('\r\n')
    results=[]
    result=[]
    for i in dataSpliting:
        #print(i)
        columns=i.split(',')
        result.append(columns)
        #print(result)
    reader=csv.DictReader(dataSpliting)
    for row in reader:
        #print(row)
        results.append(dict(row))
        

    #print(results)    
    fieldsnames=[key for key in results[0].keys()]
    if 'message' and 'name'and'contact' not in fieldsnames:
        #print("Please Check file , three fields are required to move further i.e Name , Contact and , Message . if fields are present then check heading No other Name is allowed")
        flash("Please Check file , three fields are required to move further i.e Name , Contact and , Message . if field are present then check heading No other Name is allowed")
        return redirect (url_for('main.mapping'))
    else:
        for ind , val in enumerate(fieldsnames):
            if val.lower()=='contact':
                number=ind
            if val.lower()=='message':
                message=ind
            if val.lower()=='name':
                name1=ind  
                    
        for record in results:
                

            # check record will see that the file record is already stored into the table Content or not 
            #if ... it already exist the it will not save the same data again
            # else ... it will save the record into the table
            
            check_record=Content.query.filter_by(number=record[fieldsnames[number]],message=record[fieldsnames[message]],name=record[fieldsnames[name1]],file_id=file_id.id).first()
            if check_record:
                pass
            else:
                add=Content(number=record[fieldsnames[number]],message=record[fieldsnames[message]],name=record[fieldsnames[name1]],file_id=file_id.id)
                db.session.add(add)
                db.session.commit()
            
    # redirect to the attachment page which will give the option to the user to attach image or document  with mesage file
    return render_template('attachment.html',file_id=file_id.id)  
    
   


@main.route('/main/<int:file_id>/<attachment>/attachment_upload')
def attachment_upload(file_id,attachment):
    '''
    The photo and document button redirect to this function 
    and this function redirect to the attachment upload page where user attach the attachment with the file 
    this data will save into the database having table Attachment and also save ito the floder taht is on the system
    '''
    #print(attachment)
    return render_template('attachment_upload.html',file_id=file_id,attachment=attachment)

#allowed photo extension function
def allowed_photo_extension(filename):
    '''
    This function will check the file extension of the Image 
    This application only allow png,jpg and jpeg files
    '''
    photo_extension= set(['png','jpg','jpeg'])
    return '.' in filename and filename.rsplit('.',1)[1].lower() in photo_extension 

#allowed document extension function
def allowed_document_extension(filename):
    '''
    This function will check the file extension of the document
    This application only allows xlsx , csv , docx and pdf 
    '''
    document_extension= set(['xlsx','csv','docx','pdf'])
    return '.' in filename and filename.rsplit('.',1)[1].lower() in document_extension    



#uploadig photo into the database
@main.route('/main/<int:file_id>/<attach>/save_attachment',methods = ["POST"])    
def save_attachment(file_id,attach):
    '''
    This function will Upload the file into the database table (Attachment ) and also on the systen in FOLDER=D:/FLASK/upload/
    if conditions are give for Photo and Document upload
    '''
    #print(attach)

    #if user want to attach Photo with the file
    if attach=="photo":
        FOLDER="D:/FLASK/upload/"
        
        if 'file' not in request.files: 
            flash(" No file Part")  # when no file found the this message will be flashed
            
        file=request.files['file']    # get the file from the page

        if file.filename=='':         
            flash(" No image selected for uploading")    # when no file is selected
        
        if file and allowed_photo_extension(file.filename):   # if file is found and have the given extension
            filename=secure_filename(file.filename)
            print(filename)
            #mimetype=file.mimetype
            file.save(os.path.join("D:/FLASK/upload", filename))  # save file to the given folder

            # check that , the selected file is alreday there or not in the table and in the photo attribute is empty(NULL)
            # if yes... then save file to that row, it helps to reduce the duplicate record
            find_id=Attachment.query.filter_by(file_id=file_id, photo_name='Null').first()  
             
            if find_id:
                find_id.photo_name=filename
                db.session.commit()
                flash("image Successfully uploaded")
            else:    
                upload_photo=Attachment(file_id=file_id,photo_name=filename)            
                db.session.add(upload_photo)
                db.session.commit()
                flash("image Successfully uploaded")
            return render_template('attachment.html',file_id=file_id)
        else:            
            flash(" Please check the image type Only= png , jpg,jpeg allowed")


    # if the user wnt to attach document with the file
    if attach=="document":
        FOLDER="D:/FLASK/upload/"
        
        if 'file' not in request.files:
            flash(" No file Part")
            
        file=request.files['file']

        if file.filename=='':
            flash(" No document selected for uploading")
        
        if file and allowed_document_extension(file.filename):
            filename=secure_filename(file.filename)
            print(filename)
            #mimetype=file.mimetype
            file.save(os.path.join("D:/FLASK/upload", filename))

            find_id=Attachment.query.filter_by(file_id=file_id, document_name='Null').first()
            if find_id:
                find_id.document_name=filename
                db.session.commit()
                flash("Document Successfully uploaded")
            else:    
                upload_photo=Attachment(file_id=file_id,document_name=filename)            
                db.session.add(upload_photo)
                db.session.commit()
                flash("Document Successfully uploaded")
           
            
            return render_template('attachment.html',file_id=file_id)
        else:            
            flash(" Please check the image type Only='xlsx','csv','docx','pdf' allowed")        
            

    return render_template('attachment_upload.html',file_id=file_id,attachment=attach)
    
    
'''
When start button is pressed the automation Code will be start
'''

#AUTOMATON CODE

def message(browser,msg):
    '''
    This function will send the message from the file
    it will target the input box of the message ,copy the message from the file and send it
    to copy the message we are using the Pyperclip because it will help to send the emojis also.
    if we simply take the message and it has emoji then it will give error. So Pyperclip is help to handel this error
    '''
    print("Message function")
    input_xpath='//div[@contenteditable="true"][@data-tab="9"]'  # path of the message box

    input_box=browser.find_element_by_xpath(input_xpath)   # select the messsage box
                    #input_box= WebDriverWait(browser,500).until(EC.presence_of_element_located((By.XPATH,input_xpath)))
    time.sleep(3)
    pyperclip.copy(msg)     # copy the message into the clip board
    input_box.send_keys(Keys.CONTROL+"v")   # paste it into the message box
    time.sleep(3)
    input_box.send_keys(Keys.ENTER)         #press enter key to send the message
    time.sleep(3)   

def photo(browser,pic):
    '''
    This function ,attach the Photo
    It will target the attach ment box and then find the image option and select the picture from the uploaded folder 
    '''
    time.sleep(3)
    #Click Attachment Box
    attachment_box = browser.find_element_by_xpath('//div[@title="Attach"]')
    attachment_box.click()
    time.sleep(3)
    #Select Image Icon
    image_box = browser.find_element_by_xpath('//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]') 
    #attach file                         
    image_box.send_keys("D:/FLASK/upload/"+pic)
    time.sleep(3)

def photo2(browser,pic2):
    '''
    If we have multiple file of picture to attach then this function will be called
    it will target the add button and attach the multiple file
    '''
    #Select the Add button
    addfile_button=browser.find_element_by_xpath('//input[@accept="*"]')
    #attch picture
    addfile_button.send_keys("D:/FLASK/upload/"+pic2)
    time.sleep(3)

def document(browser, doc):
    '''
    This function ,attach the document
    It will target the attach ment box and then find the document option and select the document from the uploaded folder 
    '''

    time.sleep(3)
    #Click Attachment Box
    attachment_box = browser.find_element_by_xpath('//div[@title="Attach"]')
    attachment_box.click()
    time.sleep(3)
    #Select Document Icon
    document_box = browser.find_element_by_xpath('//input[@accept="*"]') 
    #attach the file                           
    document_box.send_keys("D:/FLASK/upload/"+doc)
    time.sleep(3)
    
def document2(browser,doc2):
    '''
    If we have multiple file of documents to attach then this function will be called
    it will target the add button and attach the multiple file
    '''
    addfile_button=browser.find_element_by_xpath('//input[@accept="*"]')
    addfile_button.send_keys("D:/FLASK/upload/"+doc2)
    time.sleep(3)
    




@main.route('/main/<int:file_id>/automation/')
def automation(file_id):
    file=History.query.all()
    
    options2=webdriver.ChromeOptions()
    
    options2.add_argument(CHROME_PROFILE_PATH) #Settind option so that we don't need to Scan QR code again and again
    options2.add_experimental_option('excludeSwitches', ['enable-logging'])
    browser=webdriver.Chrome('D:/FLASK/minor_project/chromedriver.exe' ,options=options2) # Using Chrome driver
    browser.maximize_window()
    browser.get('https://web.whatsapp.com/') # getting the whatassapp web url
    
    
    #record=Content.query.all()   #fectch the all record

    record=Content.query.filter(Content.file_id==file_id) # fetch the only matching id record
    Photo= Attachment.query.filter(Attachment.file_id==file_id) #fetch the attachment record
    #print(file_id)

    #Photo_record store the list of the photo name of that file 
    Photo_record=[row.photo_name  for row in Photo if row.photo_name !='Null']
    
    #document_record store the list of the document name of that file
    document_record=[row.document_name  for row in Photo if row.document_name !='Null']
    print(document_record)

    number=[row.number for row in record]
    #print(record)
    
    
    for row in record:
            try:
                if(len(str(row.number))!=10):  #if the length of the number is not 10 then Wrong number status will be updated to the table the code will stope
                    row.status="Fail,Wrong number"    
                    db.session.commit()
                else:   
                    #link will search the number through url
                    time.sleep(5)
                    link = "https://web.whatsapp.com/send?phone="+"+91"+str(row.number)
                        
                    #WebDriverWait(browser,500).until(link)
                    browser.get(link)
                    time.sleep(5) 
                    
                    #if the photo is attached with the file this condition will run
                    if Photo_record:
                        
                        # list1=[]
                        # for p1 in Photo:
                        #     list1.append(p1.photo_name)
                        # print(list1)    
                        print(Photo_record)
                        time.sleep(7)
                        try:
                       
                            for photo1 in range(len(Photo_record)):
                                if(photo1==0):
                                    photo(browser,Photo_record[0])     #call photo functiom                          
                                    #print("first "+list1[0])
                                
                                if(photo1<len(Photo_record) and photo1 !=0):
                                    print(Photo_record[photo1])
                                    photo2(browser,Photo_record[photo1])   #call photo2 function for multiple file

                            #targetting the send button        
                            send_path=   '//span[@data-icon="send"]'    
                            send_button= WebDriverWait(browser,500).until(EC.presence_of_element_located((By.XPATH,send_path)))
                            #send_button =browser.find_element_by_xpath(send_path)
                            send_button.click()
                            
                            
                            #print('Done')
                            #change the staus of the Photo
                            row.photo_status='Done'
                            db.session.commit()
                        except:
                            row.photo_status='Fail'
                            db.session.commit()

                    if document_record:    
                        print(document_record)                      
                        try:
                            for document1 in range(len(document_record)):
                                if(document1==0):
                                    document(browser,document_record[0])      #document function call                          
                                    #print("first "+list1[0])
                                
                                if(document1<len(document_record) and document1 !=0):
                                    print(document_record[document1])
                                    document2(browser,document_record[document1])  # document2 function call for multiple files

                            #target the send button        
                            send_path=   '//span[@data-icon="send"]'    
                            #send_button= WebDriverWait(browser,500).until(EC.presence_of_element_located((By.XPATH,send_path)))
                            send_button =browser.find_element_by_xpath(send_path)
                            send_button.click()
                            
                            #print('Done')
                            row.document_status='Done'
                            db.session.commit()
                        except:
                            row.document_status='Fail'
                            db.session.commit()

                    time.sleep(2) 
                    print(row.message)
                    message(browser,row.message)
                    row.status='Done'
                    db.session.commit()        
                    
                    
            except NoSuchElementException:
                #print("Failed to send message")  
                row.status="Fail"    
                db.session.commit()

    browser.quit()

    return redirect(url_for('main.status'))

@main.route('/status')    
def status():
    '''
    This function will redirect to the Status page , where we can download the Status report of the send messages
    '''

    file=History.query.all()
    return render_template('status.html',file=file)

@main.route('/main/<int:file_id>/download_report/') 
def download_report(file_id):
    '''
    This will help to create the staus file in Excel format
    '''

    record=Content.query.filter(Content.file_id==file_id)
    file_name=History.query.with_entities(History.file_name).filter(History.id==file_id).scalar()
    #print(file_name)
    
    #print(row.status)
    output=io.BytesIO() #output in bytes
    workbook=xlwt.Workbook() #create workbook object
    sheet=workbook.add_sheet(file_name) #adding sheet

    #adding headings
    sheet.write(0,0,'Name')
    sheet.write(0,1,'Number')
    sheet.write(0,2,"Message Status")
    sheet.write(0,3,"Photo Status")
    sheet.write(0,4,"Document Status")
    index=0

    #inserting record
    for row in record:
        sheet.write(index+1,0,row.name)
        sheet.write(index+1,1,row.number)
        sheet.write(index+1,2,row.status)
        sheet.write(index+1,3,row.photo_status)
        sheet.write(index+1,4,row.document_status)
        index+=1
    workbook.save(output)  #savethe sheet
    output.seek(0)   
    
    return Response(output,mimetype="application/ms-excel",headers={"Content-Disposition":"attachment;filename=Report.xls"})
    #return redirect(url_for('main.status'))    


@main.route('/history')
def history():
    history_data=History.query.all()
    data=[row.date_posted.date() for row in history_data]
    #print(data)
    

    return render_template('history.html',record=history_data)

def delete_content(file_id):
    print(file_id)
    Content.query.filter_by(file_id=file_id).delete()   
    db.session.commit()

def delete_attach(file_id):
    print(file_id)
    Attachment.query.filter_by(file_id=file_id).delete()
    db.session.commit()    


@main.route('/main/<int:id>/delete/')
def delete(id):
    print(id)
    file_id1=History.query.get_or_404(id)    
    delete_content(id)
    delete_attach(id)
    
    db.session.delete(file_id1)
    db.session.commit()
    
    return redirect(url_for('main.history'))   

