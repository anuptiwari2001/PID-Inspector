export interface SampleFile {
  id: string;
  file: string;
  title: string;
  route: string;
  blurb: string;
}

export const SAMPLES: SampleFile[] = [
  {
    id: "crude",
    file: "crude-unit.proteus.xml",
    title: "Crude unit feed",
    route: "Proteus",
    blurb: "Blank service, a duplicate tag, a broken reference, and a line with one recorded end.",
  },
  {
    id: "cooling",
    file: "cooling-water.proteus.xml",
    title: "Cooling water",
    route: "Proteus",
    blurb: "A small sheet that loads cleanly and passes the project checks.",
  },
  {
    id: "dexpi2",
    file: "dexpi-2-stub.xml",
    title: "DEXPI 2.0.1 stub",
    route: "DEXPI 2",
    blurb: "Shows the version boundary. Tags only — relationships are not interpreted.",
  },
  {
    id: "plant3d",
    file: "plant3d-export.json",
    title: "Plant 3D extract",
    route: "AutoCAD",
    blurb: "SDK-style JSON. Plant 3D does not export P&ID XML.",
  },
  {
    id: "csv",
    file: "plant3d-datamanager.csv",
    title: "Data Manager CSV",
    route: "AutoCAD",
    blurb: "The same checks, fed from a column extract instead of XML.",
  },
  {
    id: "pdf",
    file: "feed-sheet.pdf",
    title: "PDF text layer",
    route: "PDF",
    blurb: "Tags stay unreviewed until you confirm them. A PDF is not a DEXPI file.",
  },
];
