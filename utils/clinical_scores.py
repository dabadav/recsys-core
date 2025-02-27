# clinical_scores.py
# import plotly.graph_objects as go
from models.patient import Patient, ARAT, MoCA
import numpy as np
import matplotlib.pyplot as plt

# class ClinicalScoresAnalyzer:
#     @staticmethod
#     def create_arat_radar(arat: ARAT) -> go.Figure:
#         categories = ['Grasp', 'Grip', 'Pinch', 'Gross Movement']
#         values = [arat.grasp/18, arat.grip/12, arat.pinch/18, arat.gross_movement/9]

#         fig = go.Figure()
#         fig.add_trace(go.Scatterpolar(
#             r=values,
#             theta=categories,
#             fill='toself',
#             name='ARAT Scores'
#         ))

#         fig.update_layout(
#             polar=dict(
#                 radialaxis=dict(
#                     visible=True,
#                     range=[0, 1]
#                 )),
#             showlegend=False,
#             title="ARAT Subscales"
#         )
#         return fig

#     @staticmethod
#     def create_moca_radar(moca: MoCA) -> go.Figure:
#         categories = ['Visuospatial', 'Naming', 'Memory', 'Attention',
#                      'Language', 'Abstraction', 'Delayed Recall', 'Orientation']
#         max_values = [5, 3, 5, 6, 3, 2, 5, 6]
#         values = [
#             moca.visuospatial/5, moca.naming/3, moca.memory/5,
#             moca.attention/6, moca.language/3, moca.abstraction/2,
#             moca.delayed_recall/5, moca.orientation/6
#         ]

#         fig = go.Figure()
#         fig.add_trace(go.Scatterpolar(
#             r=values,
#             theta=categories,
#             fill='toself',
#             name='MoCA Scores'
#         ))

#         fig.update_layout(
#             polar=dict(
#                 radialaxis=dict(
#                     visible=True,
#                     range=[0, 1]
#                 )),
#             showlegend=False,
#             title="MoCA Subscales"
#         )
#         return fig

import matplotlib.pyplot as plt
import numpy as np

class ClinicalScoresAnalyzer:
    @staticmethod
    def create_arat_radar(arat: ARAT) -> plt.Figure:
        """
        Create a radar chart for ARAT subscales using Matplotlib.
        """
        categories = ['Grasp', 'Grip', 'Pinch', 'Gross Movement']
        values = [arat.grasp / 18, arat.grip / 12, arat.pinch / 18, arat.gross_movement / 9]

        # Number of variables
        num_vars = len(categories)

        # Compute angle for each axis
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]  # Close the loop

        # Initialize the radar chart
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

        # Draw one axe per variable and add labels
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        plt.xticks(angles[:-1], categories)

        # Draw ylabels
        ax.set_rscale('linear')
        ax.set_rlabel_position(0)
        plt.yticks([0.25, 0.5, 0.75, 1], ["25%", "50%", "75%", "100%"], color="grey", size=8)
        plt.ylim(0, 1)

        # Plot data
        values += values[:1]  # Close the loop
        ax.plot(angles, values, linewidth=2, linestyle='solid', label='ARAT Scores')
        ax.fill(angles, values, 'b', alpha=0.1)

        # Add a title
        plt.title("ARAT Subscales", size=14, y=1.1)

        return fig

    @staticmethod
    def create_moca_radar(moca: MoCA) -> plt.Figure:
        """
        Create a radar chart for MoCA subscales using Matplotlib.
        """
        categories = ['Visuospatial', 'Naming', 'Memory', 'Attention',
                      'Language', 'Abstraction', 'Delayed Recall', 'Orientation']
        values = [
            moca.visuospatial / 5, moca.naming / 3, moca.memory / 5,
            moca.attention / 6, moca.language / 3, moca.abstraction / 2,
            moca.delayed_recall / 5, moca.orientation / 6
        ]

        # Number of variables
        num_vars = len(categories)

        # Compute angle for each axis
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]  # Close the loop

        # Initialize the radar chart
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

        # Draw one axe per variable and add labels
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        plt.xticks(angles[:-1], categories)

        # Draw ylabels
        ax.set_rscale('linear')
        ax.set_rlabel_position(0)
        plt.yticks([0.25, 0.5, 0.75, 1], ["25%", "50%", "75%", "100%"], color="grey", size=8)
        plt.ylim(0, 1)

        # Plot data
        values += values[:1]  # Close the loop
        ax.plot(angles, values, linewidth=2, linestyle='solid', label='MoCA Scores')
        ax.fill(angles, values, 'r', alpha=0.1)

        # Add a title
        plt.title("MoCA Subscales", size=14, y=1.1)

        return fig