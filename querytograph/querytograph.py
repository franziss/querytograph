import pandas as pd
import re, os, sys
import traceback
import numpy as np
import gradio as gr
from rapidfuzz import fuzz
from langchain.prompts.prompt import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from os import listdir
from os.path import isfile, join

class QueryToGraph():
    
    def __init__(self):
        pass


    def find_df(self, data_path, table_name):
        ## Find the most similar file
        onlyfiles = [f for f in listdir(data_path) if isfile(join(data_path, f))]
        valid_files = []
        for i in onlyfiles:
            if table_name in i.lower():
                try:
                    pd.read_pickle(data_path+i)
                    valid_files.append((i,fuzz.ratio(i, table_name)))
                except:
                    try:
                        pd.read_csv(data_path+i)
                        valid_files.append((i,fuzz.ratio(i, table_name)))
                    except:
                        pass
        return valid_files

    def generate_codes(self, query, data_path, table_name, openai_api_key=None, err_msg=None):

        if openai_api_key is None:
            openai_api_key = os.environ['OPENAI_API_KEY']

        #os.environ["GPT_MODEL"] = "gpt-3.5-turbo"
        ## Init the llm and prompt template
        llm = OpenAI(openai_api_key=openai_api_key,
                    model_name="gpt-3.5-turbo")

        if err_msg is None:
            _DEFAULT_TEMPLATE = """I have a dataframe with these columns {columns}

            Give me the pandas code to perform the following:
            1. {query}. Assume the dataframe is already available and it is under variable df.
            2. plot the results in plotly. Do not show code of pip installing plotly. Do not use matplotlib or cufflinks        

            """
            prompt = PromptTemplate(
                input_variables=["query", "columns"], template=_DEFAULT_TEMPLATE)    

        else:
            _DEFAULT_TEMPLATE = """I have a dataframe with these columns {columns}
            
            Give me the pandas code to perform the following:
            1. {query}. Assume the dataframe is already available and it is under variable df.
            2. plot the results in plotly. Do not show code of pip installing plotly. Do not use matplotlib or cufflinks        

            Your previous generated code has the following error message {err_msg}
            Fix the errors/bugs and you must give me the right code this time!
            """
            prompt = PromptTemplate(
                input_variables=["query", "columns", "err_msg"], template=_DEFAULT_TEMPLATE)    

        print("--- Query")
        print(query)
        print("--- Err_msg")
        print(err_msg)
        chain = LLMChain(llm=llm, prompt=prompt)

        valid_files = self.find_df(data_path, table_name)

        if len(valid_files) > 0:
            # sort and read the first file that has the most similar name
            valid_files.sort(key=lambda x:-x[1])
            print(f'Reading file: {data_path+valid_files[0][0]}')
            df = pd.read_pickle(data_path+valid_files[0][0])            

            if query != '':
                ## Call OpenAI api to generate the codes
                #print(prompt.format_prompt(query=query, columns=list(df.columns)).to_messages())
                result = chain.run(query=query, columns=list(df.columns), err_msg=err_msg)
                print('OpenAI results')
                print(result)

                global global_result
                global_result = result

                # Use regular expression to extract substrings between ```
                code_blocks = re.findall(r'```(.*?)```', result, flags=re.DOTALL)

                # Print the extracted code blocks
                print("code_blocks")
                code_blocks1 = []
                for code_block in code_blocks:
                    code_blocks1.append(code_block.replace('python','').strip())
                    print(code_block.replace('python','').strip())               
            else:
                return None, df     
        else:
            raise FileExistsError(f'No matching file for {data_path}{table_name}')

        return code_blocks1, df

    def generate_chart(self, query_textbox, data_path_textbox, tablename_textbox, openai_api_key=None, err_msg=None):  
        """
        Main entry point of the class
        
        Parameters
        ----------
        query_textbox : str
            Question by the user, which will be used to generate the graph
        data_path_textbox : str
            Folder which contains Pandas dataframes in csv or pkl (pickle)
        tablename_textbox : str
            Filename of the dataframe that the user wants to query on.
            Do not require the exact name


        Returns
        ------
        fig : Plotly figure object
            The actual figure based on query_textbox
        """  
        try:
            print('HELLO')
            code_blocks1, df = self.generate_codes(query_textbox, data_path_textbox, tablename_textbox, openai_api_key, err_msg)
            #print(df)
            table = df.tail()#.to_dict(orient='records')

            if code_blocks1 is None:
                return None, table
                        
            globals()['df']=df
            loc = {}    
            # execute the code        
            for code_block in code_blocks1:
                print(code_block.strip())
                exec(code_block.strip(), globals(), loc)
            print("loc:{loc}")
            try:
                return loc['fig'], table # str(list(df.columns))
            except:
                return loc['figure'], table #str(list(df.columns))
        except Exception:
            print('Start recursive exception!!!')
            etype, evalue, tb = sys.exc_info()
            err_msg = traceback.format_exception_only(etype, evalue)[-1]
            print(err_msg)
            return self.generate_chart(query_textbox, data_path_textbox, tablename_textbox, openai_api_key, err_msg)


    """
    def list_columns(data_path_textbox, tablename_textbox):  
        valid_files = find_df(data_path_textbox, tablename_textbox)

        if len(valid_files) > 0:
            # sort and read the first file that has the most similar name
            valid_files.sort(key=lambda x:-x[1])
            print(f'Reading file: {data_path_textbox+valid_files[0][0]}')
            df = pd.read_pickle(data_path_textbox+valid_files[0][0])            
            return str(list(df.columns))
        else:
            return ''
    """

def run_gr():
    """
    Launch a Gradio where user can input their queries
    """
    query_textbox = gr.inputs.Textbox(label="Query. Click submit with empty query to show the preview of the data")
    data_path_textbox = gr.inputs.Textbox(label="Data Folder", default="./")
    tablename_textbox = gr.inputs.Textbox(label="Table Name", default="vgt")
    output_textbox = gr.Dataframe(row_count = (5, "dynamic"), col_count = (1, "dynamic"))
    #button = gr.Button(label="Display Columns")

    qtg = QueryToGraph()

    interface = gr.Interface(fn=qtg.generate_chart, 
                                inputs=[query_textbox, data_path_textbox, tablename_textbox],
                                outputs=["plot", output_textbox])
    """
    def callback_1(data_path_textbox, tablename_textbox):
        output_text = list_columns(data_path_textbox, tablename_textbox)
        return output_text

    interface.input_interfaces[1].button_connect(callback_1)
    """
    interface.launch(show_error=True)



if __name__ == "__main__":
    
    run_gr()