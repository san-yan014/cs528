import mysql.connector
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import numpy as np

DB_HOST = '127.0.0.1'
DB_USER = 'root'
DB_PASSWORD = 'hw5password123'
DB_NAME = 'requests'

def load_data():
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT r.gender, r.age, m.country, r.income 
        FROM requests_normalized r
        JOIN ip_country_mapping m ON r.ip_id = m.ip_id
        WHERE r.income > 0 AND r.age > 0 AND r.gender IS NOT NULL AND r.gender != ''
    """)
    data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return data

def train_model():
    print("loading data...")
    data = load_data()
    
    print(f"total samples: {len(data)}")
    
    gender_encoder = LabelEncoder()
    country_encoder = LabelEncoder()
    
    genders = [row[0] for row in data]
    ages = [row[1] for row in data]
    countries = [row[2] for row in data]
    incomes = [row[3] for row in data]
    
    gender_encoded = gender_encoder.fit_transform(genders)
    country_encoded = country_encoder.fit_transform(countries)
    
    X = np.column_stack([gender_encoded, ages, country_encoded])
    y = np.array(incomes)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"training samples: {len(X_train)}")
    print(f"test samples: {len(X_test)}")
    print(f"unique income values: {len(np.unique(y))}")
    
    print("\ntraining random forest classifier...")
    model = RandomForestClassifier(n_estimators=200, max_depth=20, random_state=42)
    model.fit(X_train, y_train)
    
    predictions = model.predict(X_test)
    
    correct = sum([1 for p, a in zip(predictions, y_test) if p == a])
    accuracy = correct / len(y_test) * 100
    
    print(f"\nmodel 2: income prediction")
    print(f"accuracy: {accuracy:.2f}%")
    print(f"correct: {correct}/{len(y_test)}")
    
    with open('model2_results.txt', 'w') as f:
        f.write(f"model 2: income prediction (random forest)\n")
        f.write(f"features: gender, age, country\n")
        f.write(f"accuracy: {accuracy:.2f}%\n")
        f.write(f"correct predictions: {correct}/{len(y_test)}\n")
        f.write(f"training samples: {len(X_train)}\n")
        f.write(f"test samples: {len(X_test)}\n")
        f.write(f"unique income values: {len(np.unique(y))}\n")
        f.write(f"\nsample predictions:\n")
        for i in range(min(20, len(X_test))):
            match = "✓" if predictions[i] == y_test[i] else "✗"
            f.write(f"  {match} actual: {y_test[i]}, predicted: {predictions[i]}\n")
    
    print("results saved to model2_results.txt")
    
    return accuracy

if __name__ == '__main__':
    accuracy = train_model()
    if accuracy < 40:
        print(f"warning: accuracy {accuracy:.2f}% is below 40% target")
    else:
        print(f"success: accuracy {accuracy:.2f}% meets 40% requirement")
