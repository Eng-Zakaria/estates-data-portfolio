let
    Source = Parquet.Document(File.Contents(GoldFolder & "\dim_date.parquet"))
in
    Source
