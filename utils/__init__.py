# clinical_scores.py
import plotly.graph_objects as go
from models.patient import ARAT, MoCA

class ClinicalScoresAnalyzer:
    @staticmethod
    def create_arat_radar(arat: ARAT) -> go.Figure:
        categories = ['Grasp', 'Grip', 'Pinch', 'Gross Movement']
        values = [arat.grasp/18, arat.grip/12, arat.pinch/18, arat.gross_movement/9]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='ARAT Scores'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=False,
            title="ARAT Subscales"
        )
        return fig

    @staticmethod
    def create_moca_radar(moca: MoCA) -> go.Figure:
        categories = ['Visuospatial', 'Naming', 'Memory', 'Attention',
                     'Language', 'Abstraction', 'Delayed Recall', 'Orientation']
        max_values = [5, 3, 5, 6, 3, 2, 5, 6]
        values = [
            moca.visuospatial/5, moca.naming/3, moca.memory/5,
            moca.attention/6, moca.language/3, moca.abstraction/2,
            moca.delayed_recall/5, moca.orientation/6
        ]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='MoCA Scores'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=False,
            title="MoCA Subscales"
        )
        return fig
