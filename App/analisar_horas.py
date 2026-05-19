from data_processor import DataProcessor
import pandas as pd

processor = DataProcessor('aruba.txt')
matrix = processor.get_matrix_for_model()
inv_mapping = {v: k for k, v in processor.label_mapping.items()}

matrix['hour'] = matrix.index.hour if hasattr(matrix.index, 'hour') else matrix['hour']
matrix['activity'] = matrix['label_encoded'].map(inv_mapping)

print(matrix[matrix['hour'] == 13]['activity'].value_counts())