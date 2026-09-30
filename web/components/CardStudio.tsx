"use client";
import Ico from "./Ico";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { Card, EntitlementOption } from "@/lib/api";
import type { SheetSpec } from "@/lib/art";
import { CardDeco } from "./DecoAnim";
import CharacterSheet, { type ArtProps, type Char, type TryOn } from "./CharacterSheet";
import PlayerCard from "./PlayerCard";
import { useT } from "./I18n";

type DecoImages = { avatar: Record<string, string>; card: Record<string, string> };
type Draft = { motto: string; nameplate: string; avatar_frame: string; card_frame: string; title: string; featured: string[]; public: boolean };
type Kind = "nameplate" | "avatar_frame" | "card_frame" | "title";
type Mode = "view" | "profile" | "wardrobe";

/** The player card page. View mode: the card and three buttons. Edit profile: a draft (motto, colour, decorations,
 *  featured achievements, private or public) previews on the card and is saved in one request. Edit wardrobe: the
 *  closet opens under the card and the card is the preview: whatever you try on shows there at once. */
export default function CardStudio({ initial, sheet, badges, deco, shareUrl, wardrobe }:
  { initial: Card; sheet: SheetSpec | null; badges: Record<string, string | null>; deco: DecoImages; shareUrl: string;
    wardrobe: { char: Char; art: ArtProps } | null }) {
  const t = useT();
  const router = useRouter();
  const [c, setC] = useState<Card>(initial);
  const fromCard = (x: Card): Draft => ({ motto: x.motto, nameplate: x.nameplate_id, avatar_frame: x.avatar_frame, card_frame: x.card_frame, title: x.title_id, featured: x.cosmetics.featured ?? x.featured.map((a) => a.key), public: x.public });
  const [draft, setDraft] = useState<Draft>(fromCard(initial));
  const [mode, setMode] = useState<Mode>("view");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [hover, setHover] = useState<{ kind: Kind; o: EntitlementOption } | null>(null);
  const [tryOn, setTryOn] = useState<TryOn | null>(null);
  const opts = c.entitlements;

  // the server re-renders the page after wardrobe changes; take the fresh card unless a profile draft is open
  useEffect(() => { if (mode !== "profile") { setC(initial); setDraft(fromCard(initial)); } }, [initial]);  // eslint-disable-line react-hooks/exhaustive-deps

  const plate = opts.nameplate.find((o) => o.id === draft.nameplate);
  const titleOpt = opts.title.find((o) => o.id === draft.title);
  const preview: Card = {
    ...c, motto: draft.motto, nameplate: plate?.value ?? c.nameplate, nameplate_id: draft.nameplate,
    avatar_frame: draft.avatar_frame, avatar_frame_art: opts.avatar_frame.find((o) => o.id === draft.avatar_frame)?.art ?? null,
    card_frame: draft.card_frame, card_frame_art: opts.card_frame.find((o) => o.id === draft.card_frame)?.art ?? null,
    title_id: draft.title, title: titleOpt && titleOpt.id !== "none" ? titleOpt.name : null,
    featured: draft.featured.map((k) => c.earned_achievements.find((a) => a.key === k)).filter(Boolean) as Card["featured"],
  };
  const wearing = mode === "wardrobe" && tryOn ? { ...c, worn: { ...c.worn, id: tryOn.outfit.id, name: tryOn.outfit.name, color: tryOn.outfit.color, art_id: tryOn.outfit.art_id }, style: tryOn.style, body: tryOn.body } : null;
  const wardrobeDirty = !!tryOn && (tryOn.outfit.id !== c.worn.id || tryOn.style !== c.style || tryOn.body !== c.body);
  const wardrobeBlocked = !!tryOn && !tryOn.outfit.owned;
  async function saveWardrobe() {
    if (!tryOn) return;
    if (await patch({ wear: tryOn.outfit.id, style: tryOn.style, appearance: { body: tryOn.body } })) { setMode("view"); setTryOn(null); }
  }
  function cancelWardrobe() { setMode("view"); setTryOn(null); setErr(null); }
  const shown = mode === "profile" ? preview : wearing ?? c;
  const shownSheet = mode === "wardrobe" && tryOn ? tryOn.sheet : sheet;
  const cardArt = (shown.card_frame_art && deco.card[shown.card_frame_art]) || null;
  const avatarArt = (shown.avatar_frame_art && deco.avatar[shown.avatar_frame_art]) || null;

  async function patch(body: Record<string, unknown>) {
    setBusy(true); setErr(null);
    const r = await fetch("/api/me/character", { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    if (!r.ok) { setBusy(false); setErr((await r.json()).detail ?? t("Could not save that.")); return false; }
    const j: Card = await fetch("/api/me/card").then((x) => x.json());   // the card shape, whatever the patch returned
    setBusy(false); setC(j); setDraft(fromCard(j)); router.refresh(); return true;
  }
  async function save() {
    if (await patch({ banner: draft.motto, nameplate: draft.nameplate, avatar_frame: draft.avatar_frame, card_frame: draft.card_frame, title: draft.title, featured: draft.featured, public: draft.public })) setMode("view");
  }
  function cancel() { setDraft(fromCard(c)); setMode("view"); setErr(null); }
  function toggleFeat(key: string) {
    setDraft((d) => ({ ...d, featured: d.featured.includes(key) ? d.featured.filter((k) => k !== key) : [...d.featured, key].slice(-3) }));
  }
  async function copy() {
    try { await navigator.clipboard.writeText(shareUrl); setCopied(true); setTimeout(() => setCopied(false), 1500); } catch { /* the field can be copied by hand */ }
  }
  const dirty = JSON.stringify(draft) !== JSON.stringify(fromCard(c));
  const owned = (k: Kind) => opts[k].filter((o) => o.owned).length;
  const detail = (k: Kind) => {
    const o = hover?.kind === k ? hover.o : opts[k].find((x) => x.id === draft[k]);
    if (!o) return null;
    return <div className="pick-detail"><b>{t(o.name)}</b>{o.desc ? <span className="muted"> · {t(o.desc)}</span> : null}{o.owned ? <span className="muted"> · {o.id === draft[k] ? t("selected") : o.granted ? t("granted by staff") : t("entitled")}</span> : <span style={{ color: "var(--warn)" }}> · 🔒 {o.hint ? t(o.hint) : null}</span>}</div>;
  };
  const tile = (k: Kind, o: EntitlementOption) => ({
    type: "button" as const, disabled: busy || !o.owned, title: o.owned ? t(o.name) : `${t(o.name)} · ${o.hint ? t(o.hint) : o.hint}`,
    className: `pick ${draft[k] === o.id ? "on" : ""} ${o.owned ? "" : "locked"}`,
    onMouseEnter: () => setHover({ kind: k, o }), onMouseLeave: () => setHover(null), onFocus: () => setHover({ kind: k, o }), onBlur: () => setHover(null),
    onClick: () => o.owned && setDraft((d) => ({ ...d, [k]: o.id })),
  });

  return (
    <div className="studio">
      <div className={`studio-card ${cardArt ? "framed" : ""}`}>
        <CardDeco src={cardArt} theme={shown.card_frame} />
        <PlayerCard c={shown} sheet={shownSheet} badges={badges} deco={{ avatar: avatarArt, card: null, avatarTheme: shown.avatar_frame }} />
      </div>

      {mode === "view" && (
        <div className="studio-actions">
          <button className="primary" onClick={() => setMode("profile")}><Ico group="utility" id="edit" />{t("Edit profile")}</button>
          {wardrobe && <button onClick={() => setMode("wardrobe")}><Ico group="navigation" id="wardrobe" />{t("Edit wardrobe")}</button>}
          <Link className="btn" href={`/members/${c.id}`}><Ico group="utility" id="public" />{t("View as others")}</Link>
        </div>
      )}

      {mode === "wardrobe" && wardrobe && (
        <div className="studio-panel">
          <div className="row" style={{ justifyContent: "space-between", marginBottom: 10 }}>
            <div><div className="eyebrow">{t("Editing your wardrobe")}</div><div className="small muted">{t("Pick a set, weapons and build; the card shows them. Nothing is kept until you press Save.")}</div></div>
            <div className="row" style={{ gap: 6 }}>
              <button onClick={cancelWardrobe} disabled={busy}>{t("Cancel")}</button>
              <button className="primary" onClick={saveWardrobe} disabled={busy || !wardrobeDirty || wardrobeBlocked} title={wardrobeBlocked ? t("That set is not earned yet") : undefined}>{busy ? t("Saving…") : t("Save")}</button>
            </div>
          </div>
          <CharacterSheet key={`${c.worn.id}-${c.style}-${c.body}`} initial={wardrobe.char} fallbackColor={c.nameplate} art={wardrobe.art} mirror={false} deferred onPreview={setTryOn} />
          {err && <div className="note small" data-tone="error" style={{ marginTop: 10, borderColor: "var(--bad)" }}>{err}</div>}
        </div>
      )}

      {mode === "profile" && (
        <div className="card studio-panel editor">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div>
              <div className="eyebrow">{t("Editing your profile")}</div>
              <div className="small muted">{t("Changes show on the card as you pick. Nothing is kept until you press Save. Locked items are entitlements you have not earned yet.")}</div>
            </div>
            <div className="row" style={{ gap: 6 }}>
              <button onClick={cancel} disabled={busy}>{t("Cancel")}</button>
              <button className="primary" onClick={save} disabled={busy || !dirty}>{busy ? t("Saving…") : t("Save")}</button>
            </div>
          </div>

          <div className="edit-grid" style={{ marginTop: 6 }}>
            <div>
              <label className="small muted" htmlFor="motto" style={{ display: "block", marginTop: 12 }}>{t("Motto (40 letters)")}</label>
              <input id="motto" type="text" value={draft.motto} maxLength={40} onChange={(e) => setDraft((d) => ({ ...d, motto: e.target.value }))} placeholder={t("Something short and true")} style={{ width: "100%", marginTop: 4 }} />

              <div className="pick-head"><span className="small muted">{t("Nameplate colour")}</span><span className="small muted">{owned("nameplate")}/{opts.nameplate.length}</span></div>
              <div className="pick-grid">
                {opts.nameplate.map((o) => (
                  <button key={o.id} {...tile("nameplate", o)} aria-label={t(o.name)} style={{ width: 28, height: 28, borderRadius: "50%", background: o.value }}>
                    {!o.owned && <span className="pick-lock">🔒</span>}
                  </button>
                ))}
              </div>
              {detail("nameplate")}

              <div className="pick-head"><span className="small muted">{t("Title · shown after your name")}</span><span className="small muted">{owned("title") - 1}/{opts.title.length - 1}</span></div>
              <div className="pick-grid">
                {opts.title.map((o) => (
                  <button key={o.id} {...tile("title", o)} className={`pick pick-title ${draft.title === o.id ? "on" : ""} ${o.owned ? "" : "locked"}`}>
                    {o.id === "none" ? t("None") : t(o.name)}{!o.owned && " 🔒"}
                  </button>
                ))}
              </div>
              {detail("title")}

              <div className="pick-head"><span className="small muted">{t("Shown on the card")}</span><span className="small muted">{t("up to three")}</span></div>
              {c.earned_achievements.length ? (
                <div className="row" style={{ gap: 6 }}>
                  {c.earned_achievements.map((a) => (
                    <button key={a.key} onClick={() => toggleFeat(a.key)} disabled={busy} className={draft.featured.includes(a.key) ? "primary" : ""} title={t(a.desc)} style={{ padding: "5px 9px", fontSize: 11 }}>
                      {a.icon} {t(a.name)}
                    </button>
                  ))}
                </div>
              ) : <div className="small">{t("Nothing earned yet. Finish a quest.")}</div>}

              <div className="pick-head"><span className="small muted">{t("Profile visibility")}</span></div>
              <div className="subnav" style={{ margin: 0 }}>
                <a href="#" className={!draft.public ? "on" : ""} onClick={(e) => { e.preventDefault(); setDraft((d) => ({ ...d, public: false })); }}><Ico group="utility" id="private" />{t("Private")}</a>
                <a href="#" className={draft.public ? "on" : ""} onClick={(e) => { e.preventDefault(); setDraft((d) => ({ ...d, public: true })); }}><Ico group="utility" id="public" />{t("Public")}</a>
              </div>
              <div className="small muted" style={{ marginTop: 6 }}>{draft.public ? t("Anyone with the link can open your card.") : t("Only logged-in guild members can open your card.")}</div>
              <div className="row" style={{ gap: 8, marginTop: 8 }}>
                <input type="text" readOnly value={shareUrl} onFocus={(e) => e.currentTarget.select()} style={{ flex: 1, minWidth: 160, fontFamily: "var(--mono)", fontSize: 12 }} />
                <button type="button" onClick={copy}>{copied ? t("Copied") : t("Copy link")}</button>
              </div>
            </div>

            <div>
              <div className="pick-head"><span className="small muted">{t("Avatar frame")}</span><span className="small muted">{owned("avatar_frame")}/{opts.avatar_frame.length}</span></div>
              <div className="pick-grid">
                {opts.avatar_frame.map((o) => (
                  <button key={o.id} {...tile("avatar_frame", o)} aria-label={t(o.name)} style={{ width: 52, height: 52, borderRadius: 8 }}>
                    <span className="pick-av" />
                    {o.art && deco.avatar[o.art] ? <img className="px" src={deco.avatar[o.art]} alt="" style={{ position: "absolute", inset: 2, width: 48, height: 48 }} /> : o.id === "none" ? null : <span className="pick-swatch" />}
                    {!o.owned && <span className="pick-lock">🔒</span>}
                  </button>
                ))}
              </div>
              {detail("avatar_frame")}

              <div className="pick-head"><span className="small muted">{t("Player card frame")}</span><span className="small muted">{owned("card_frame")}/{opts.card_frame.length}</span></div>
              <div className="pick-grid">
                {opts.card_frame.map((o) => (
                  <button key={o.id} {...tile("card_frame", o)} aria-label={t(o.name)} style={{ width: 72, height: 58, borderRadius: 6 }}>
                    {o.art && deco.card[o.art] ? <img className="px" src={deco.card[o.art]} alt="" style={{ position: "absolute", inset: 3, width: 66, height: 52 }} /> : o.id === "none" ? <span className="pick-none">{t("none")}</span> : <span className="pick-swatch" />}
                    {!o.owned && <span className="pick-lock">🔒</span>}
                  </button>
                ))}
              </div>
              {detail("card_frame")}
            </div>
          </div>
          {err && <div className="note small" data-tone="error" style={{ marginTop: 10, borderColor: "var(--bad)" }}>{err}</div>}
        </div>
      )}
    </div>
  );
}
