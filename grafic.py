import matplotlib.pyplot as plt
import pandas as pd

def price_grafic(df: pd.DataFrame, filename: str = "price_distribution.png") -> bool:
    
    plt.figure(figsize=(10, 6))
    
    prices = df[df['Цена'] > 0]['Цена']
            
    if len(prices) > 0:
        plt.hist(prices, bins=15, color='skyblue', edgecolor='black', alpha=0.7)
        plt.title('Распределение цен на аренду (Sutochno.ru)')
        plt.xlabel('Цена за ночь (₽)')
        plt.ylabel('Количество объектов')
        plt.grid(axis='y', alpha=0.75)
                
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close() 
        return True
    else:
        print("Недостаточно данных для построения графика.")
        return False

plt.figure(figsize=(10, 6))

        