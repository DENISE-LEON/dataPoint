from pydantic import BaseModel, Field, ConfigDict
from typing import List

class file_model(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    team_name: str = Field(validation_alias='Table Name')
    records_before: int = Field(validation_alias='No of Records Before')
    records_after: int = Field(validation_alias='No of Records After')
    expected_records_deleted: int = Field(validation_alias='Expected Records Deleted')
    actual_records_deleted: int = Field(validation_alias='Actual Records Deleted')


    # def delta_calculation(self):
    #     return self.expected_records_deleted - self.actual_records_deleted

def df_to_pydantic(df):
    print(f"[TRACE] df_to_pydantic called | input_rows={len(df)}")
    pydantic_rows = df.to_dict(orient='records')
    header = list(pydantic_rows[0].keys()) if pydantic_rows else []
    print(f"[TRACE] df_to_pydantic output | header_count={len(header)} row_count={len(pydantic_rows)}")
    return header, pydantic_rows

def validate_pydantic_model(rows):
    print(f"[TRACE] validate_pydantic_model called | row_count={len(rows)}")
    invalid_fields = []
    for idx, row in enumerate(rows):
        try:
            file_row = file_model.model_validate(row)
            _ = file_row
        except Exception as e:
            print(f"[ERROR] Row validation failed at index={idx}: {str(e)}")
            invalid_fields.append(row)
            continue
    print(f"[TRACE] validate_pydantic_model complete | invalid_count={len(invalid_fields)}")
    return invalid_fields

def mappings_to_pydantic_header(mappings, rows):
    print(f"[TRACE] mappings_to_pydantic_header called | mapping_count={len(mappings)} row_count={len(rows)}")
    rows = [{mappings.get(k, k): v for k, v in row.items()} for row in rows]
    print("[TRACE] mappings_to_pydantic_header complete")
    return rows

required_aliases = {
    field.validation_alias
    for field in file_model.model_fields.values()
    if isinstance(field.validation_alias, str)
    }

print(f"[TRACE] required_aliases initialized | count={len(required_aliases)}")