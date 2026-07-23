import pytest
from shared.data_loader import ... DataLoader
import pandas as pd

@pytest.fixture
def sample_data():
    return pd.DataFrame({
        'data': ['2023-01-01', '2023-01-08'],
        'n1': [1, 10],
        'n2': [2, 20],
        'n3': [3, 30],
        'n4': [4, 40],
        'n5': [5, 50],
        'n6': [6, 60]
    })

def test_data_validation(sample_data):
    loader = DataLoader()
    loader.raw_data = sample_data
    loader._validate_data()
    
    # Test intervallo numeri
    sample_data.loc[0, 'n1'] = 100
    with pytest.raises(ValueError):
        loader._validate_data()
