import os
import pandas as pd

def load_data():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_directory, 'student_data2.csv')
    data = pd.read_csv(csv_path)
    return data


def load_data2():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_directory, 'student_learning_skills_updated.csv')
    data2 = pd.read_csv(csv_path)
    return data2