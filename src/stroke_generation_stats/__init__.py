

import matplotlib.pyplot as plt

class StrokeGenerationStats:
    def __init__(self):
        self.events = {}
    
    def count(self, event_name: str):
        if event_name not in self.events:
            self.events[event_name] = 0
        self.events[event_name] += 1

    def plot(self):
        """Generates a circular donut chart of the counted events."""
        if not self.events:
            print("No events to plot.")
            return

        # Extract data
        labels = list(self.events.keys())
        sizes = list(self.events.values())
        
        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(6, 6))
        
        # Define a clean, modern color palette
        colors = plt.cm.get_cmap('Set3')(range(len(labels)))

        # Plot the pie chart
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            autopct=lambda p: f'{int(p * sum(sizes) / 100)}', # Shows exact counts instead of %
            startangle=90, 
            colors=colors,
            textprops=dict(color="black"),
            wedgeprops=dict(width=0.4, edgecolor='white') # 'width' creates the donut hole
        )

        # Style the text inside the slices
        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_weight('bold')

        ax.set_title("Stroke Generation Events", fontsize=14, weight='bold', pad=20)
        
        # Ensure the chart is a perfect circle
        ax.axis('equal')  
        plt.tight_layout()
        plt.show()