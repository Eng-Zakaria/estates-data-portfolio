// Split the comma-joined fault types on the scorecard into one row per
// finding, so the exceptions page can count findings by fault type.
// Result column: types_1, types_2, ... (variable arity, up to 7 labels).
let
    Source = Parquet.Document(File.Contents(P16Folder & "\building_scorecard.parquet")),
    Promoted = Table.PromoteHeaders(
        Source, [PromoteAllScalars = true]
    ),
    Cleaned = Table.TransformColumnTypes(Promoted, {
        {"meter_id", type text},
        {"building", type text},
        {"source", type text},
        {"peak", type number},
        {"types", type text},
        {"kwh_year", type number},
        {"gbp_year", type number}
    }),
    Exploded = Table.SplitColumn(
        Cleaned, "types", Splitter.SplitTextByCommas(",")
    )
in
    Exploded