// Isso é uma página praticamente.

// Imports
import { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMapEvents } from 'react-leaflet';

// Coordenadas aproximadas do centro de Maricá, RJ, para visualização inicial
const maricaCenter = [-22.9186, -42.8186];

// Componente para lidar com cliques no mapa
function MapClickHandler({ onMapClick }) {
    useMapEvents({
        click(e) {
            onMapClick(e.latlng);
        },
    });
    return null;
}

// Componente principal do site
function MapDisplay() {

    const [startPoint, setStartPoint] = useState(null);
    const [endPoint, setEndPoint] = useState(null);
    const [pathSegments, setPathSegments] = useState([]); // Estado para os segmentos da rota

    // Estados para os controles da UI
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [networkType, setNetworkType] = useState('drive');
    const [optimizeFor, setOptimizeFor] = useState('length');
    const [avgSpeed, setAvgSpeed] = useState('');
    const [isMenuOpen, setIsMenuOpen] = useState(false); // Estado para o menu mobile

    // Estados para os resultados da rota
    const [totalDistance, setTotalDistance] = useState(null);
    const [totalTime, setTotalTime] = useState(null);

    const handleMapClick = (latlng) => {
        if (!startPoint) setStartPoint(latlng);
        else if (!endPoint) setEndPoint(latlng);
        else {
            setStartPoint(latlng);
            setEndPoint(null);
        }
        setPathSegments([]);
        setError('');
    };

    const fetchRoute = async () => {
        if (!startPoint || !endPoint) {
            setError("Por favor, selecione um ponto de partida e um de destino.");
            return;
        }
        setLoading(true);
        setError('');
        setPathSegments([]);

        const params = new URLSearchParams({
            start_lat: startPoint.lat,
            start_lon: startPoint.lng,
            end_lat: endPoint.lat,
            end_lon: endPoint.lng,
            optimize_for: optimizeFor,
        });

        // Adiciona a velocidade média apenas se o campo for preenchido
        if (avgSpeed) {
            params.append('average_speed_kmh', avgSpeed);
        }
        
        const apiUrl = `http://localhost:7777/api/pequod/pathfinder/${networkType}/?${params}`;

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || `Erro na API: ${response.statusText}`);
            }
            const data = await response.json();
            
            if (data.path_segments && data.path_segments.length > 0) {
                setPathSegments(data.path_segments);
                setTotalDistance(data.total_length_meters);
                setTotalTime(data.total_time_minutes);
            } else {
                setError(data.error || "Nenhum caminho encontrado.");
            }
        } catch (err) {
            setError(err.message || "Falha ao buscar a rota.");
        } finally {
            setLoading(false);
        }
    };

    const clearPoints = () => {
        setStartPoint(null);
        setEndPoint(null);
        setPathSegments([]);
        setError('');
        setTotalDistance(null);
        setTotalTime(null);
    };

    return (
        <div className="flex flex-col md:flex-row h-screen bg-slate-50 font-sans">
            {/* Painel de Controle (Lateral) */}
            <div className="w-full md:w-96 p-4 md:p-6 bg-white shadow-lg md:overflow-y-auto shrink-0">
                <div className="flex justify-between items-center mb-4">
                    <h1 className="text-2xl font-bold text-slate-800">Pequod</h1>
                    {/* Botão do menu dropdown visível apenas em telas pequenas (mobile) */}
                    <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="md:hidden p-2 rounded-md hover:bg-slate-100">
                        <svg className="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"} />
                        </svg>
                        <span className="sr-only">Abrir menu de opções</span>
                    </button>
                </div>
                
                <p className="text-sm text-slate-600 mb-6 hidden md:block">Selecione o ponto de partida e destino no mapa.</p>
                
                {/* Container das OPÇÕES, que será ocultado/mostrado em mobile */}
                <div className={`${isMenuOpen ? 'block' : 'hidden'} md:block`}>
                    <div className="space-y-4 mb-6">
                        <div>
                            <label htmlFor="networkType" className="block text-sm font-medium text-slate-700">Tipo de rede</label>
                            <select id="networkType" value={networkType} onChange={(e) => setNetworkType(e.target.value)} className="mt-1 block w-full p-2 border border-slate-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
                                <option value="drive">Carro</option>
                                <option value="bike">Bicicleta</option>
                                <option value="walk">Caminhada</option>
                                <option value="all">Todos (All)</option>
                            </select>
                        </div>
                        <div>
                            <label htmlFor="optimizeFor" className="block text-sm font-medium text-slate-700">Otimizar para</label>
                            <select id="optimizeFor" value={optimizeFor} onChange={(e) => setOptimizeFor(e.target.value)} className="mt-1 block w-full p-2 border border-slate-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
                                <option value="length">Distância (Mais Curto)</option>
                                <option value="time">Tempo (Mais Rápido)</option>
                            </select>
                        </div>
                        <div>
                            <label htmlFor="avgSpeed" className="block text-sm font-medium text-slate-700">Velocidade média (km/h) <span className="text-xs text-slate-500">(Opcional)</span></label>
                            <input type="number" id="avgSpeed" value={avgSpeed} onChange={(e) => setAvgSpeed(e.target.value)} placeholder="Ex: 60" className="mt-1 block w-full p-2 border border-slate-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
                        </div>
                    </div>
                </div>

                {/* Botões e resultados agora ficam FORA do container do menu */}
                <div className="flex space-x-3">
                    <button onClick={fetchRoute} disabled={!startPoint || !endPoint || loading} className="flex-1 px-4 py-2 bg-blue-600 text-white font-semibold rounded-md shadow-sm hover:bg-blue-700 disabled:bg-slate-400 disabled:cursor-not-allowed transition-colors">
                        {loading ? 'Calculando...' : 'Encontrar Rota'}
                    </button>
                    <button onClick={clearPoints} className="px-4 py-2 bg-slate-600 text-white font-semibold rounded-md shadow-sm hover:bg-slate-700 transition-colors">
                        Limpar
                    </button>
                </div>

                {error && <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-md text-sm">{error}</div>}
                
                {totalDistance !== null && !error && (
                    <div className="mt-4 p-3 bg-slate-100 text-slate-800 rounded-md space-y-1">
                        <p><strong>Distância:</strong> {(totalDistance / 1000).toFixed(2)} km</p>
                        <p><strong>Tempo Estimado:</strong> {totalTime.toFixed(1)} minutos</p>
                    </div>
                )}
            </div>

            {/* Mapa */}
            <div className="flex-1 h-full w-full">
                <MapContainer center={maricaCenter} zoom={13} className="h-full w-full">
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; OpenStreetMap' />
                    <MapClickHandler onMapClick={handleMapClick} />
                    
                    {startPoint && <Marker position={startPoint}><Popup>Ponto de Partida</Popup></Marker>}
                    {endPoint && <Marker position={endPoint}><Popup>Ponto de Destino</Popup></Marker>}
                    
                    {pathSegments.map((segment, index) => {
                        const isAffected = !!segment.applied_condition;
                        const pathColor = isAffected ? '#F97316' : '#2563EB'; // Laranja e Azul do Tailwind
                        const coordinates = segment.coordinates.map(c => [c.lat, c.lon]);

                        return (
                            <Polyline key={index} positions={coordinates} color={pathColor} weight={5} opacity={0.8}>
                                {isAffected && (
                                    <Popup><b>Condição:</b> {segment.applied_condition.description}</Popup>
                                )}
                            </Polyline>
                        );
                    })}
                </MapContainer>
            </div>
        </div>
    );
}

export default MapDisplay;