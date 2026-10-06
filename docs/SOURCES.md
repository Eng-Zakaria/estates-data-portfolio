# COBie spec reference (verified 2026-10-06)

Source: buildingSMART COBie (https://www.buildingsmart.org/standards/cobie/) and UK BIM Framework.

Sheets expected: Contact, Facility, Floor, Space, Zone, Type, Component, System, Assembly, Connection, Spare, Resource, Job, Impact, Document, Attribute, Coordinate, Issue, Picture.

Key relationships:
- Component → Type (via TypeName)
- Component → Space (via SpaceName, may be multi-value)
- Space → Floor (via FloorName)
- System → Component (via ComponentNames)
- Job → Type (via TypeName)
- CreatedBy → Contact (via email or name)

Mandatory columns (verified against COBie v2.4):
- Contact: CreatedOn, CreatedBy, Category, Email, Phone, Company, Department, OrganizationCode, GivenName, FamilyName
- Facility: Name, CreatedOn, CreatedBy, Category, ProjectName, SiteName, LinearUnits, AreaUnits, VolumeUnits, CurrencyUnit, AreaMeasurement, ExternalSystem, ExternalProjectObjectId, ExternalProjectId, ExternalFacilityObjectId, ExternalFacilityId, Description, ProjectDescription, Phase
- Floor: Name, CreatedOn, CreatedBy, Category, FloorNumber, Height
- Space: Name, CreatedOn, CreatedBy, Category, FloorName, Description, RoomTag, UsableHeight, GrossArea, NetArea
- Type: Name, CreatedOn, CreatedBy, Category, Description, AssetType, Manufacturer, ModelNumber, WarrantyDurationParts, WarrantyDurationLabor, ExpectedLife, DurationUnit, WarrantyDescription, SpareParts, OperationManual, Model, PredefinedType, StartDate, EndDate, IsProjected, ReplacementCost, ExpectedDuration, DurationUnit, WarrantyDuration, WarrantyDurationUnit, WarrantyDescription
- Component: Name, CreatedOn, CreatedBy, Category, TypeName, Space, Description, SerialNumber, InstallationDate, WarrantyStartDate, TagNumber, AssetIdentifier, BarCode, Color, Comment
