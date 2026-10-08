// GoldFolder = parameter, e.g. C:\...\data\gold (or the repo data\gold path).
let
    Source = Parquet.Document(File.Contents(GoldFolder & "\mart_asset_health.parquet"))
in
    Source
