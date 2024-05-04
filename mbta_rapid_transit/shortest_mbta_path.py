import networkx as nx
import pandas as pd


class MBTA():
    def __init__(self):
        df = pd.read_csv('data/MBTA_Rapid_Transit_Stop_Distances.csv')
        self.gr, self.stop_id_from_name, self.stop_name_from_id = self._create_graph(df)

    def _create_graph(self, df: pd.DataFrame):
        """Create a networkx graph from MBTA data"""
        gr = nx.Graph()
        stop_id_from_name, stop_name_from_id = {}, {}
        for _, row in df.iterrows():
            for direction in ['from', 'to']:
                stop_id_from_name[row[f'{direction}_stop_name']] = row[f'{direction}_stop_id']
                stop_name_from_id[row[f'{direction}_stop_id']] = row['route_id'] + ' ' + row[f'{direction}_stop_name']

        gr.add_nodes_from(stop_id_from_name.keys())
        edges = [(row['from_stop_id'], row['to_stop_id'], row['from_to_miles'])
                 for _, row in df.iterrows()]
        gr.add_weighted_edges_from(edges)

        # Now we have added the individual lines, but we have not
        # considered passing BETWEEN lines. Let's add a 10 minute
        # penalty. If the average speed of a stop is 3 minutes + 20 mph
        # Let's consider a stop at 3 miles
        stations = df.groupby('from_station_id')['route_id'].apply('unique')
        stations = stations.loc[stations.apply(len) > 1]

        for station, lines in stations.to_dict().items():
            for i, l1 in enumerate(lines):
                for j, l2 in enumerate(lines[i+1:]):
                    row1 = df.loc[(df['from_station_id'] == station) &
                                 (df['route_id'] == l1)]
                    row2 = df.loc[(df['from_station_id'] == station) &
                                 (df['route_id'] == l2)]
                    for k, r1 in row1.iterrows():
                        for l, r2 in row2.iterrows():
                            gr.add_edge(r1['from_stop_id'], r2['from_stop_id'], weight=3)

        return gr, stop_id_from_name, stop_name_from_id
    
    def calculate_route(self, stop1: str, stop2: str):
        """Get the route from one station to another"""
        id1 = self.stop_id_from_name.get(stop1, None)
        id2 = self.stop_id_from_name.get(stop2, None)
        if id1 is None or id2 is None:
            raise ValueError('Stops not found')
        
        path = nx.shortest_path(self.gr, id1, id2, 'weight')
        return [self.stop_name_from_id[v] for v in path]
    

if __name__ == '__main__':
    mbta = MBTA()
    print(mbta.calculate_route('Copley', 'Airport'))