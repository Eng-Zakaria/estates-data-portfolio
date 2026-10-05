let
    Source = Parquet.Document(File.Contents(GoldFolder & "\dim_emission_factor.parquet"))
in
    Source
