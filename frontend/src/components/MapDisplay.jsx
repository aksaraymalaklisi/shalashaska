import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMapEvents } from 'react-leaflet';

// Coordenadas aproximadas do centro de Maricá, RJ
const maricaCenter = [-22.9186, -42.8186]; 

// Componente wrapper para usar useMapEvents (forma correta de lidar com cliques no mapa)
function MapClickHandler({ onMapClick }) { // Import dinâmico para evitar problemas no lado do servidor se houver
    const map = useMapEvents({
        click(e) {
            onMapClick(e);
        },
    });
    return null;
}

// O componente MapDisplay por padrão irá usar o MapClickHandler.
function MapDisplay() {
    const [startPoint, setStartPoint] = useState(null);
    const [endPoint, setEndPoint] = useState(null);
    const [path, setPath] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleMapClick = (e) => {
        if (!startPoint) {
            setStartPoint(e.latlng);
            setPath([]); 
            setError('');
        } else if (!endPoint) {
            setEndPoint(e.latlng);
        } else { 
            setStartPoint(e.latlng);
            setEndPoint(null);
            setPath([]);
            setError('');
        }
    };

    const fetchRoute = async () => {
        if (!startPoint || !endPoint) {
            setError("Por favor, selecione um ponto de partida e um de destino.");
            return;
        }
        setLoading(true);
        setError('');
        setPath([]);

        const params = new URLSearchParams({
            start_lat: startPoint.lat,
            start_lon: startPoint.lng,
            end_lat: endPoint.lat,
            end_lon: endPoint.lng,
        });
        const apiUrl = `http://127.0.0.1:8000/api/pequod/pathfinder/?${params.toString()}`;

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || `Erro na API: ${response.statusText}`);
            }
            const data = await response.json();
            if (data.path_coordinates && data.path_coordinates.length > 0) {
                const leafletPath = data.path_coordinates.map(coord => [coord.lat, coord.lon]);
                setPath(leafletPath);
            } else {
                setError(data.error || "Nenhum caminho encontrado ou caminho vazio retornado.");
            }
        } catch (err) {
            console.error("Erro ao buscar rota:", err);
            setError(err.message || "Falha ao buscar a rota.");
        } finally {
            setLoading(false);
        }
    };

    const clearPoints = () => {
        setStartPoint(null);
        setEndPoint(null);
        setPath([]);
        setError('');
    }

    return (
        <div>
        <div style={{ marginBottom: '10px', padding: '10px', border: '1px solid #ccc', borderRadius: '5px' }}>
            <h4>Planejador de Rotas</h4>
            <p>Clique no mapa para definir o ponto de partida, depois o ponto de destino.</p>
            {startPoint && <p><strong>Partida (Clique):</strong> Lat: {startPoint.lat.toFixed(5)}, Lng: {startPoint.lng.toFixed(5)}</p>}
            {endPoint && <p><strong>Destino (Clique):</strong> Lat: {endPoint.lat.toFixed(5)}, Lng: {endPoint.lng.toFixed(5)}</p>}
            <button onClick={fetchRoute} disabled={!startPoint || !endPoint || loading} style={{padding: '8px 12px', marginRight: '10px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                {loading ? 'Calculando...' : 'Encontrar Rota'}
            </button>
            <button onClick={clearPoints} style={{padding: '8px 12px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer'}}>
                Limpar Pontos
            </button>
            {error && <p style={{ color: 'red', marginTop: '10px' }}>Erro: {error}</p>}
        </div>

        <MapContainer 
            center={maricaCenter} // Lembre-se de que maricaCenter deve estar definido
            zoom={13} 
            style={{ height: 'calc(100vh - 200px)', width: '100%', border: '1px solid #000' }}
        >
            <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            <MapClickHandler onMapClick={handleMapClick} /> {/* Componente para lidar com cliques */}
            
            {/* Marcadores para os pontos clicados pelo usuário */}
            {startPoint && <Marker position={startPoint}><Popup>Ponto de Partida (Seu clique)</Popup></Marker>}
            {endPoint && <Marker position={endPoint}><Popup>Ponto de Destino (Seu clique)</Popup></Marker>}
            
            {/* Polyline para a rota principal calculada */}
            {path.length > 0 && <Polyline positions={path} color="blue" weight={5} />}

            {/* NOVAS POLYLINES PARA CONECTAR OS CLIQUES À ROTA */}
            {/* Linha do clique de partida até o início real da rota */}
            {startPoint && path.length > 0 && path[0] && (
              <Polyline
                positions={[[startPoint.lat, startPoint.lng], path[0]]} 
                // path[0] é o primeiro ponto [lat, lng] da rota calculada
                color="green" // Ou uma cor que indique "início"
                weight={3}
                dashArray="5, 5" // Faz a linha ser pontilhada/tracejada
              />
            )}

            {/* Linha do clique de destino até o fim real da rota */}
            {endPoint && path.length > 0 && path[path.length - 1] && (
              <Polyline
                positions={[[endPoint.lat, endPoint.lng], path[path.length - 1]]} 
                // path[path.length - 1] é o último ponto [lat, lng] da rota calculada
                color="red" // Ou uma cor que indique "fim"
                weight={3}
                dashArray="5, 5"
              />
            )}
        </MapContainer>
    </div>
    );
}

export default MapDisplay;