import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import mysql.connector
import io

connection=mysql.connector.connect(host="localhost",user="root",password="12345",database="project1")
mycursor=connection.cursor()


icon= Image.open(r"C:\Users\Paranthaman\OneDrive\Documents\4.png")
st.set_page_config(page_title="BizCard: Extracting Business Card Data with OCR",
                   page_icon=icon,layout='wide',
                   initial_sidebar_state='expanded',menu_items={'About':"This is OCR app which created by Paranthaman"})

st.markdown("<h1 style='text-align: center; color: Green;'>BizCardX: Extracting Business Card Data with OCR</h1>",unsafe_allow_html=True)

selected=option_menu(None,["HOME","UPLOAD AND MODIFY"],
                     icons=["house","cloud-upload","pencil-square"],
                     default_index=0,
                     orientation="horizontal",
                     styles={"nav-link":{"text-algin":"center","font-size":"25px"},
                             "icon":{"font-size":"25px"},
                             "nav-link-selected":{"background-color":"#ff5757"}})


if selected=="HOME":
    col1,col2=st.columns(2)
    with col1:
        st.image(Image.open(r"C:\Users\Paranthaman\OneDrive\Documents\image config.jpg"))
        st.markdown("## :green[**Technologies Used :**] Python,easy OCR, Streamlit, SQL, Pandas")
    with col2:
        st.write(
        "## :green[**About :**] Bizcard is a Python application designed to extract information from business cards.")
        st.write(
        '## The main purpose of Bizcard is to automate the process of extracting key details from business card images, such as the name, designation, company, contact information, and other relevant data. By leveraging the power of OCR (Optical Character Recognition) provided by EasyOCR, Bizcard is able to extract text from the images.')


def extracted_text(result):
    ext_data={'name':[],'Designtion':[],'Address':[],'website':[],'pincode':[],'contact':[],'email':[],'company_name':[]}
    ext_data['name'].append(result[0])
    ext_data['Designtion'].append(result[1])
    for m in range(2,len(result)):
        if '+' in result[m] or (result[m].replace('-', '').isdigit() and '-' in result[m]):
            ext_data['contact'].append(result[m])
        elif '@' in result[m] and '.com' in result[m]:
            small=result[m].lower()
            ext_data['email'].append(small)
        elif result[m].isdigit():
                ext_data['pincode'].append(result[m])
        elif 'www' in result[m] or 'WWW' in result[m] or 'wWW' in result[m] :
             ext_data['website'].append(result[m])
        elif re.match(r'^[A-Za-z]', result[m]):
                ext_data['company_name'].append(result[m]) 
        else:
            remove_colon=re.sub(r'[,;]','',result[m])
            ext_data['Address'].append(remove_colon)

    for key,value in ext_data.items():
         if len(value)>0:
              concatenated_string=' '.join(value)
              ext_data[key]=[concatenated_string]
         else:
              value='NA'
              ext_data[key]=[value]
    return ext_data


if selected=="UPLOAD AND MODIFY":
    image=st.file_uploader(label="upload the image",type=['jpg','jpeg','PNG'])

    @st.cache_data
    def load_image():
        reader=easyocr.Reader(['en'],model_storage_directory='.')
        return reader
    
    reader_1 = load_image()
    if image is not None:
     input_image = Image.open(image)
    # Setting Image size
    st.image(input_image, width=350, caption='Uploaded Image')

    result = reader_1.readtext(np.array(input_image), detail=0)
    #create dataframe
    ext_text=extracted_text(result)
    df=pd.DataFrame(ext_text)
    st.dataframe(df)

        # Converting image into bytes
    image_bytes = io.BytesIO()
    input_image.save(image_bytes, format='PNG')
    image_data = image_bytes.getvalue()
    # Creating dictionary
    data = {"Image": [image_data]}
    df_1 = pd.DataFrame(data)
    concat_df = pd.concat([df,df_1], axis=1)
    #st.dataframe(concat_df)

    #preview the extracted data
    
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        selected = option_menu(
            menu_title=None,
            options=["Preview"],
            icons=['file-earmark'],
            default_index=0,
            orientation="horizontal"
        )

        ext_text = extracted_text(result)
        df = pd.DataFrame(ext_text)
    if selected == "Preview":
        col_1, col_2 = st.columns([4, 4])
        with col_1:
            modified_n = st.text_input('name', ext_text["name"][0])
            modified_d = st.text_input('Designtion', ext_text["Designtion"][0])
            modified_c = st.text_input('company_name', ext_text["company_name"][0])
            modified_con = st.text_input('contact', ext_text["contact"][0])
            concat_df["name"], concat_df["Designtion"], concat_df["company_name"], concat_df[
                "contact"] = modified_n, modified_d, modified_c, modified_con
        with col_2:
            modified_m = st.text_input('email', ext_text["email"][0])
            modified_w = st.text_input('website', ext_text["website"][0])
            modified_a = st.text_input('Address', ext_text["Address"][0])
            modified_p = st.text_input('pincode', ext_text["pincode"][0])
            concat_df["email"], concat_df["website"], concat_df["Address"], concat_df[
                "pincode"] = modified_m, modified_w, modified_a, modified_p

        col3, col4 = st.columns([4, 4])
        with col3:
            Preview = st.button("Preview modified text")
        with col4:
            Upload = st.button("Upload")
        if Preview:
            filtered_df = concat_df[
                ['name', 'Designtion', 'company_name', 'contact', 'email', 'website', 'Address', 'pincode']]
            st.dataframe(filtered_df)
        else:
            pass

        if Upload:
            mycursor.execute('''create table if not exists busi_card(NAME VARCHAR(50), DESIGNATION VARCHAR(100),
                        COMPANY_NAME VARCHAR(100), CONTACT VARCHAR(35), EMAIL VARCHAR(100), WEBSITE VARCHAR(100), ADDRESS TEXT, PINCODE VARCHAR(100))''')
            connection.commit()

            P='''insert into busi_card(NAME, DESIGNATION,COMPANY_NAME, CONTACT, EMAIL, WEBSITE, ADDRESS, PINCODE)
                        values(%s,%s,%s,%s,%s,%s,%s,%s)'''
            for index, i in concat_df.iterrows():
                result_tables=(i[0],i[1],i[2],i[3],i[4],i[5],i[6],i[7])
                mycursor.execute(P,result_tables)
                connection.commit()
                st.success("successfully uploaded")
    
        