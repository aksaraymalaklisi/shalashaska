from rest_framework import serializers

class PathfindingRequestSerializer(serializers.Serializer):
    """
    Este serializador valida os parâmetros de query para a API de pathfinding.
    Ele garante que todas as coordenadas necessárias são fornecidas e são números válidos.
    """
    start_lat = serializers.FloatField(
        required=True,
        help_text="Latitude do ponto de partida."
    )
    start_lon = serializers.FloatField(
        required=True,
        help_text="Longitude do ponto de partida."
    )
    end_lat = serializers.FloatField(
        required=True,
        help_text="Latitude do ponto de destino."
    )
    end_lon = serializers.FloatField(
        required=True,
        help_text="Longitude do ponto de destino."
    )
    average_speed_kmh = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="Velocidade média em km/h para cálculo de tempo (opcional)."
    )

    def validate(self, data):
        """
        Adiciona validações customizadas, se necessário.
        Por exemplo, verificar se as latitudes/longitudes estão dentro de um intervalo válido.
        """
        if not -90 <= data['start_lat'] <= 90 or not -90 <= data['end_lat'] <= 90:
            raise serializers.ValidationError("Latitude deve estar entre -90 e 90.")
        if not -180 <= data['start_lon'] <= 180 or not -180 <= data['end_lon'] <= 180:
            raise serializers.ValidationError("Longitude deve estar entre -180 e 180.")
        return data
