let
    Source = Parquet.Document(File.Contents(GoldFolder & "\dim_asset.parquet"))
in
    Source
