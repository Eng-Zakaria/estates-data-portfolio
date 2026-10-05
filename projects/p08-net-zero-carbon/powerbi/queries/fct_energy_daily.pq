// GoldFolder = parameter, e.g. C:\...\data\gold (or the repo data\gold path).
// One query per gold table; keep names identical to the mart names.
let
    Source = Parquet.Document(File.Contents(GoldFolder & "\fct_energy_daily.parquet"))
in
    Source
