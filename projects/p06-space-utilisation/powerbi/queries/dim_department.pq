let
    Source = Parquet.Document(File.Contents(GoldFolder & "\dim_department.parquet"))
in
    Source
