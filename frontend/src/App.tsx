import { AppShell } from "./components/AppShell";

export default function App() {
  return (
    <AppShell>
      <section className="shell-placeholder" aria-labelledby="shell-heading">
        <p className="label-caps">Frontend foundation</p>
        <h1 id="shell-heading">HeatShift</h1>
        <p>
          The evidence-driven municipal planning experience is loading its first chapter.
        </p>
      </section>
    </AppShell>
  );
}
