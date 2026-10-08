// GoldFolder = parameter, e.g. C:\...\data\gold (or the repo data\gold path).
let
    Source = Parquet.Document(File.Contents(GoldFolder & "\dim_trade.parquet"))
in
    Source
