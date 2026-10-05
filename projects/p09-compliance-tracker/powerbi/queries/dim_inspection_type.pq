let
    Source = Parquet.Document(File.Contents(GoldFolder & "\dim_inspection_type.parquet"))
in
    Source
