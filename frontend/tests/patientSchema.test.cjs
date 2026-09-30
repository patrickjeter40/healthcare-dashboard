const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { createRequire } = require("node:module");
const path = require("node:path");
const { test } = require("node:test");
const ts = require("typescript");

// Execute the form's TypeScript conversion functions using the existing compiler.
const schemaPath = path.resolve(__dirname, "../src/forms/patientSchema.ts");
const { outputText } = ts.transpileModule(readFileSync(schemaPath, "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS },
});
const schema = {};
new Function("exports", "require", outputText)(
  schema,
  createRequire(schemaPath),
);

const patient = {
  first_name: "Test",
  last_name: "Patient",
  date_of_birth: "1980-01-01",
  status: "active",
  last_visit_at: "2024-01-02T18:30:45.123Z",
  allergies: [],
  conditions: [],
};

for (const zone of ["UTC", "America/Los_Angeles", "Asia/Tokyo"]) {
  test(`Unrelated edits preserve visit precision in ${zone}`, () => {
    const previousZone = process.env.TZ;
    try {
      process.env.TZ = zone;
      const values = schema.patientFormDefaults(patient);
      values.phone = "202-555-0101";
      const result = schema.toPatientWrite(
        schema.patientSchema.parse(values),
        patient,
      );
      assert.equal(result.last_visit_at, patient.last_visit_at);
      assert.equal(result.phone, values.phone);
    } finally {
      if (previousZone === undefined) delete process.env.TZ;
      else process.env.TZ = previousZone;
    }
  });
}

test("An explicitly changed visit is converted to UTC", () => {
  const values = schema.patientFormDefaults(patient);
  values.last_visit_at = "2024-02-03T12:15";
  assert.equal(
    schema.toPatientWrite(values, patient).last_visit_at,
    new Date(values.last_visit_at).toISOString(),
  );
});

test("Clearing a visit removes it", () => {
  const values = schema.patientFormDefaults(patient);
  values.last_visit_at = "";
  assert.equal(schema.toPatientWrite(values, patient).last_visit_at, null);
});

test("A new patient's visit is converted without an original record", () => {
  const values = schema.patientFormDefaults();
  values.last_visit_at = "2024-02-03T12:15";
  assert.equal(
    schema.toPatientWrite(values).last_visit_at,
    new Date(values.last_visit_at).toISOString(),
  );
});

test("An absent visit remains absent on unrelated edits", () => {
  const original = { ...patient, last_visit_at: null };
  const values = schema.patientFormDefaults(original);
  values.city = "Seattle";
  assert.equal(schema.toPatientWrite(values, original).last_visit_at, null);
});
