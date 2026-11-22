# Intake Severity

How an intake procedure rates a finding in `docs/intake-findings.md`, and how a later procedure re-rates one. Read it before you write or change a `Severity:` line. The tracker itself is defined in `references/intake/findings.md`.

Rate a finding by what its evidence shows it lets someone do in this app. The category it falls in, such as access control or hardening, sets no level by itself.

## How to rate

1. **Actor.** Who can trigger it, by the route and guard in the code: anonymous, anyone who can register (open sign-up, or every customer has an account), a specific non-staff role, staff or admin, or someone holding a secret the app does not give out.
2. **Action.** What the code lets that actor do: read, change, delete, act as another account, gain a role, lift a state, crash, compute a wrong value. "Could lead to" is not an action.
3. **Target.** Their own account, one other account by an id they must already know, many other accounts (ids are guessable or some endpoint lists them), or the whole app.
4. **Data class.** The class of what is read or changed, from "Data classes" below.
5. **Level.** Take the row in "Levels" that these facts match, then apply "Adjustments" and "Floors".

The `Severity:` line names the table row the rating comes from and any adjustment, for example `Medium (orders). Row: High, keeps access after removal; one down, staff only` or `High (billing). Row: High, changes Sensitive data of other accounts; no adjustment`. The `What:` line states the impact the rating rests on.

## Levels

| Severity | Use it for |
|----------|-----------|
| Critical | The least-privileged actor (anonymous, anyone who can register, or any ordinary account) gains admin or an equivalent role over every account, takes over any account it can name when an admin's identifier is shown or guessable, reads or changes Secret data of other accounts at scale (many accounts, by guessable or listed ids), or deletes data of every account with no way back |
| High | Someone gains a higher role or another role's powers, acts as another account, lifts or bypasses a blocking state on their own, keeps access after it was removed, reads or changes Sensitive data of other accounts, reads or changes one account's Secret or a secret the app holds (a connection string, an integration token), loses data with no way back, or moves real money wrongly. A Critical outcome only staff can reach is High |
| Medium | Someone reads or changes Ordinary data of other accounts or changes their Public data, reads a field withheld from its own role (directly, or through a search, filter or error that reveals it), or does an action reserved for another role that touches no Sensitive data; money or stock counts go wrong but can be corrected; an operation leaves bad but recoverable state; a missing control has an exploit path shown in this app |
| Low | A hardening gap with no exploit path shown, an unconfirmed advisory, wrong behavior that stores nothing, an error answered as a 500 without harm, Public data shown to the wrong user, drift, dead code, type drift, inconsistency |

These rules decide which row a finding matches:

- **A change rates like a read.** Changing another account's Sensitive data rates the same as reading it. A finding that shows only the change is High even when no read is shown.
- **Public data.** Changing another account's Public data rates as changing Ordinary data (Medium). Only showing Public data to the wrong user is Low.
- **Granting is gaining.** Giving another account a higher role rates as gaining it, with the actor who gives it.
- **Acting as another account.** Changing another account's login email or phone is acting as that account when the app's own reset flow sends to it. Cite the reset flow.
- **Known identifiers.** An email address or username counts as a known identifier. Taking over any account by one is High, and Critical when the least-privileged actor can do it and an admin's identifier is shown in the app or the repo, or is guessable.
- **Real money.** Moves real money means funds actually leave or are taken (a charge, refund or payout) without a matching order: High. A wrong stored amount that is fixed before any money moves is Medium, as a count that can be corrected. The wrong amount charged, paid or left uncollected on a real order or pay run is Medium when the app can correct it with a refund or credit, High when it cannot.
- **No way back.** A backup does not undo a loss: data changed after the last backup counts as lost. The finding names the backup config it relied on, or says the repo shows none. Deleting one kind of data from every account (all trashed items, all attachments) counts as data of every account. A defect that deletes data of every account with no way back, with no actor, rates as if the least-privileged actor did it: Critical.

Critical is narrow. Reading another account's Sensitive data is High, not Critical, however many accounts it reaches. A Critical rating cites the code for the actor, the action, the target and the data class (or the role gained), each as `path::symbol` ("Finding ids" in `findings.md`). When any of the four is inferred rather than cited, rate it High and name the missing fact in the `What:` line.

## Data classes

Classify a field by what it holds, not by its name. A column called `reason`, `notes` or `comment` holds whatever people type there.

| Class | Includes |
|-------|----------|
| Secret | Passwords and their hashes, session, reset and API tokens, API keys, signing keys, connection strings. Rate a Secret by the access it grants |
| Sensitive | Health information of any kind (visit or appointment reasons, symptoms, diagnoses, prescriptions, test results, therapy notes, and fitness, diet and sleep logs a person records about themselves), payment card data, salary and employment contracts, bank account numbers, government id numbers, legal case records, date of birth, home address, precise location, private messages, and data on religion, ethnicity, sexual life, union membership or biometrics |
| Ordinary | Account data not meant for others that does little harm if shown: preferences, lists, non-personal business records, a work email. Plans someone writes for others are Ordinary (a coach's workout or meal plan), unlike logs a person records about themselves |
| Public | Data the app shows to other users or the world by design |

## Adjustments

Only these lower a rating. Each lowers it by one level, and several together still lower it by one level in total.

- **Staff only.** Only staff or admins can trigger it, and the role check in the code excludes the app's ordinary users. In an app where every account is staff (an internal tool), its lowest role is the ordinary actor and gets no staff downgrade, and any role above the lowest counts as staff. A person who keeps access after removal is rated as they are after removal: no staff downgrade for powers that were taken away. The downgrade is for abusing a check. A defect staff hit in normal use is rated by its harm, with no staff downgrade.
- **A secret the app does not hand out.** It needs a server key, or another user's token or link. A link the app sent to the person holding it is not a leaked secret: that person using it is the ordinary case.
- **Unguessable target.** The target ids are unguessable and no endpoint returns them. An email address or username is never unguessable.
- **A control stops it first.** A control in the code stops the harm before it lands. A control that only cleans up afterwards does not count.

Nothing else lowers it. Effort is not a reason: many requests, repeated guesses, a hand-built request, or a login anyone can get. Reaching only some users, only a few records, or a field the UI hides is not a reason either.

Two cases rate differently instead of lowering:

- **Depends on deployment:** rate what the repo shows, name the setting that would change the rating, and ask for its deployed value as an Open question.
- **Depends on an unstated rule:** when the code is wrong under one reading of a rule nobody wrote down, rate it Low or make it an Open question.

## Floors

A floor holds after every adjustment. The no-way-back floor holds after the secret and unguessable-target adjustments too. A floor applies only when its outcome lands: when a control in the code stops the outcome first (a role change that waits for an owner's approval), the floor's fact is not met and the adjustment stands.

- A non-staff actor who gains a higher role is never below High.
- A non-staff actor who reads or changes Sensitive data of other accounts by guessable or listed ids is never below High.
- Data lost with no way back is never below High.

## Over-rating guards

- **Rate only what the code is shown to allow.** The action is what the evidence shows, never what it might lead to.
- **A chain needs every link.** Rate a chain of steps by its end only when every link has its own evidence. Otherwise rate the first link alone.
- **An unknown only lowers.** When a fact you could not establish would change the level, rate what the evidence supports, name the missing fact, and ask for it as an Open question. A missing fact never raises a rating.
- **Rate the reach you showed.** A library advisory, a default setting or a missing header is Low until the entry names how this app reaches it. "Applicability unconfirmed" is Low.

## Re-rating

Severity starts as the finder's first guess. A later procedure whose evidence shows a finding reaches further or less far than its rating assumes (a read beside a write, another role, Sensitive data, a guard that holds) re-rates it in the same commit as that evidence. It rewrites the `Severity:` line in both the Summary row and the finding, with the row the new rating comes from, and says so in its item report: the checklist note carries `Re-rated: F-0xx <old> -> <new> (<reason>)` for each finding it re-rated. A testing procedure in the parallel batch, which never edits the tracker, gives the new `Severity:` line and Summary row under `Tracker edits:`. An Open question asking the owner to re-rate is not a re-rate. The owner can still adjust any rating at close-out.

## Anchors

Invented examples that sit on level boundaries. Each pair differs in one fact.

| Severity | Example | Why |
|----------|---------|-----|
| Critical | In a ticket-booking app, sign-up copies every request field onto the new user, so anyone who registers with `is_staff: true` gets the staff role over every account | Anyone who can register gains an admin-equivalent role |
| High | In the same app, only box-office staff can set `is_staff` on another user, through an endpoint that skips its owner check | Same outcome, staff actor: one down |
| Critical | In a recipe-sharing app, any signed-in user can call `DELETE /recipes` with no id, which deletes every user's recipes, and the repo shows no backup | Anyone who can register deletes every account's data with no way back |
| Critical | In a team-wiki app, the password-reset endpoint takes an email and a new password and never checks the emailed token, and the About page lists the admin's email | Takeover by a known identifier, with an admin's identifier shown |
| High | The same reset flaw in a wiki whose admin emails appear nowhere in the app or repo | Takes over a named account, admin identifier not shown |
| Critical | In a payroll app, any employee can request `/users/{n}/api-token` for any number and get a token that acts as that user | Secret data of many accounts, ordinary actor |
| High | In the same app, any employee can open `/payslips/{n}` for any number and read another employee's bank account number | Sensitive, not Secret: a cross-account read is High |
| High | The payslip endpoint also accepts `PUT` from any employee, with no read shown | A change rates like a read |
| Medium | In a book-club app, any member can open `/members/{n}/shelf` and see another member's reading list | Ordinary data of other accounts |
| Medium | A store's order list lets a customer sort their own orders by `fraud_score`, a field the order view withholds from customers, so the sort order reveals it after many tries | A field withheld from your own role, through a sort; effort does not lower it |
| High | In the ticket-booking app, a customer can refund the same order twice, and the second refund pays out to their card | Funds actually leave |
| Medium | In the same app, a discount code stores a wrong price on an unpaid basket, and checkout recomputes the price before any charge | Fixed before any money moves |
| Medium | In the book-club app, any member can rename another member's public display name | Changing Public data rates as Ordinary |
| Medium | An invoicing app rounds each line before summing, so totals drift by a cent per line, and an admin edit corrects the stored invoice | Money wrong but correctable |
| Low | The session cookie lacks `SameSite`, and no cross-site request that changes state is shown | Hardening gap, no path |
| Low | A logging library in the lockfile has an advisory, and no path from a request to the vulnerable call is shown | Unconfirmed advisory |
| Low | The profile endpoint returns 500 on an empty bio and stores nothing | A 500 without harm |
