import sys
import os

# 处理 PyInstaller 运行时的路径问题
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后的路径
    base_path = sys._MEIPASS
else:
    # 普通 Python 运行环境
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

sys.path.append(base_path)

from flask import Flask, request, jsonify
import os
import sqlite3
from services.llm import LLMEngine
import json
from config.setting import CONFIG

app = Flask(__name__)
DATABASE_PATH = './app.db'

def call_back(result:list,status,template_id,task_id):
    """
    Callback function to be called when the task is completed.
    """
    print("callback:",result,status,template_id,task_id)
def create_task(file_name):
    """
    Creates a new task in the database.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, status,content) VALUES (?, ?, ?)",
        (file_name, '进行中','')
    )
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return task_id

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    File upload endpoint.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    template_id = request.form.get('template_id')
    if not template_id:
        return jsonify({"error": "Template ID is required"}), 400

    # Save the file
    storage_path = CONFIG["import_file_path"]
    if getattr(sys, 'frozen', False):
        # 如果是打包后的应用程序
        base_path = sys._MEIPASS
        storage_path = os.path.join(base_path, CONFIG["import_file_path"])
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)
        
    file_path = os.path.join(storage_path, file.filename)
    file.save(file_path)

    # Create a new task
    task_id = create_task(file.filename)
    # task_id = 1
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
    template_row = cursor.fetchone()

    preprocess_config_list = None
    llm_api_info = None

    if template_row:
        content = template_row[2]
        template_data = json.loads(content)
        workflow_row_id = template_data["workflow_id"]
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workflows WHERE id = ?", (workflow_row_id,))
        workflow_row = cursor.fetchone()
        if workflow_row:
            workflow_data = json.loads(workflow_row[2])
            llm_info = workflow_data["llm_info"]
            pre_process_infos = workflow_data["pre_process_info"]
            llm_id = llm_info["llm_id"] 
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM modeservice_table WHERE id = ?", (llm_id,))
            llm_row = cursor.fetchone()
            llm_api_info = json.loads(llm_row[2]) 
            preprocess_config_list = []
            if pre_process_infos is not None and len(pre_process_infos) > 0:
                for proc in pre_process_infos:
                    ocr_id = proc["ocr_id"]
                    try:
                        cursor = conn.cursor()
                        cursor.execute("SELECT * FROM modeservice_table WHERE id = ?", (ocr_id,)) 
                        ocr_row = cursor.fetchone()
                    except Exception as e:
                        print(e)
                        continue
                    preprocess_config_list.append({"id":ocr_row[0],"name":ocr_row[1],"api_info":ocr_row[2]})

    conn.close()

    if llm_api_info is None:
        return jsonify({
            "message": "llm api info not found",
            "task_id": task_id
        }), 500
    if preprocess_config_list is None:
        return jsonify({
            "message": "preprocess config list not found",
            "task_id": task_id
        }), 500

    llm_config = {
            "id":task_id,
            "model": llm_api_info["model"],
            "api_info": llm_api_info,
            "preprocess_infos":preprocess_config_list
        }
    print("llm_config:",llm_config)

    content = template_row[2]
    template_data = json.loads(content)
   # print(content)
    LLMEngine.run(call_back, template_data,file_path,file.filename,template_data["id"],task_id,llm_config)

    return jsonify({
        "message": "File uploaded successfully",
        "task_id": task_id
    }), 201

@app.route('/tasks', methods=['GET'])
def get_tasks():
    """
    Retrieve all tasks.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    tasks = [
        {"id": row[0], "title": row[1], "status": row[2]} for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify(tasks)

@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """
    Retrieve a specific task by ID.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({"id": row[0], "title": row[1], "status": row[2]})
    else:
        return jsonify({"error": "Task not found"}), 404

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """
    Update a specific task by ID.
    """
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({"error": "Invalid request"}), 400

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (data['status'], task_id))
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"message": "Task updated successfully"})

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """
    Delete a specific task by ID.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"message": "Task deleted successfully"})

if __name__ == '__main__':

    sys.argv[1]
    if len(sys.argv) > 1:
        DATABASE_PATH = sys.argv[1]
    else:
        raise Exception("database path not found")
    
    app.run(host='0.0.0.0', port=8000)
