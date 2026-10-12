# Onboarding a Client Company

This guide is the operator's path from an empty platform to a client company whose collaborators are answering the NOM-035 survey. Work through the steps in order — each one depends on the one before it:

1. [Create the company](#1-create-the-company), with its áreas and localidades.
2. [Add the company's users](#2-add-the-companys-users) from a CSV file.
3. [Assign the survey](#3-assign-the-survey) to the company.
4. [Hand off to the client](#4-hand-off-to-the-client) — what to send, and what each collaborator does on first login.
5. [Follow progress and close the survey](#5-follow-progress-and-close-the-survey).

Everything an operator does happens in the administration panel at `/admin/`. There is no screen inside the platform for creating companies, users or survey assignments, and client executives cannot add users themselves.

## Before you start

You need:

- **A running platform with the NOM-035 survey loaded** — see [`platform-setup.md`](platform-setup.md).
- **An operator account**: a superuser in the `Admins` group, created in [`platform-setup.md`](platform-setup.md#6-create-the-operator-account).

### Adding another operator

Operators are the only accounts created by hand; every client user comes from the CSV import in step 2.

1. In `/admin/`, go to **Cuentas → Usuarios** and click **Agregar usuario**.
2. Enter a **Nombre de usuario** (for example the email's local part, `ana.lopez`), set **Autenticación basada en contraseña** to **Habilitado**, type a password twice, and save.
3. On the page that opens, fill in:
   - **Correo electrónico** — in lowercase. Public login looks it up exactly.
   - **Nombre(s)** and **Apellido paterno**.
   - **Es staff** and **Es superusuario** — both checked. *Es staff* lets them into `/admin/`; *Es superusuario* gives them every admin permission.
   - **Grupos** — `Admins`. This is what the platform itself checks: without it the public login treats them as a collaborator with no company.
4. Save.

Operators do not need a collaborator profile or a company.

## 1. Create the company

1. Go to **Cuentas → Empresas** and click **Agregar empresa**.
2. Fill in the company data:

   | Field | |
   |---|---|
   | **Nombre comercial** | Required. The name shown throughout the platform. |
   | **Razón social** | Required. |
   | **RFC** | Optional. |
   | **Domicilio** | Optional. |
   | **Actividad principal** | Optional. |
   | **Centro de trabajo** | Optional. |
   | **Código de empresa** | **Leave it blank.** A 5-character code (uppercase letters and digits) is generated when you save. |

3. At the bottom of the page, load the company's lists:
   - **Áreas** — **at least one is required.** Each collaborator picks their área from this list when they activate their account; a company with no áreas leaves every collaborator stuck at activation with a message to contact whoever invited them.
   - **Localidades** — optional. With two or more, each collaborator picks theirs; with exactly one, it is assigned automatically and never shown; with none, the question is skipped.

   Use **Agregar otro/a** to add more rows.
4. Save, then reopen the company and **copy its Código de empresa**. You need it for the CSV file and for the hand-off.

The company list has an *Áreas* column, so a company still missing its áreas is easy to spot.

### Rules for áreas and localidades

- **Names are unique within a company**, ignoring capitalization, accents and extra spaces. `Ventas` and `ventas`, or `Dirección` and `Direccion`, are one entry typed twice, and the second is rejected. The `ñ` counts as its own letter, so `Cañada` and `Canada` can coexist.
- **To retire an entry, uncheck *activa*** — don't delete it. It disappears from the list collaborators pick from, and the people already assigned to it keep it. An entry that still has collaborators assigned cannot be deleted.
- Retiring an entry while someone is activating is safe: their submission is rejected with a message asking them to review their data, never quietly moved to another entry.

## 2. Add the company's users

Every client user — executives and employees alike — is created by importing a CSV file. The import creates the account, links it to the company, gives it its role and, when needed, generates its código de acceso, all in one step.

### Decide each person's role

| Group (in the CSV) | Shown as | What they can do |
|---|---|---|
| `Principal Exec` | Ejecutivo principal | Their company's dashboard, the roster of collaborators, the NOM-035 results, and the published reports. Answers the survey. |
| `Secondary Exec` | Ejecutivo secundario | The dashboard and the roster. No results or reports. Answers the survey. |
| `Employees` | Empleado | Answers the survey. |

Executives answer the survey too — they are workers at the company like everyone else.

### Decide how each person logs in

- **`otp`** — the person receives a login code by email each time. Use it whenever the company's email accepts external mail. Nobody handles a password.
- **`password`** — for companies that block external email, so login codes never arrive. The import generates a 9-digit **código de acceso** for each person; the company's HR hands it over internally, and the person uses it once to set their own password.

### Import

Build a file with four columns — `email`, `company_reference_code`, `group`, `auth_method` — and upload it from **Cuentas → Usuarios → Importar colaboradores**. You do not upload names, puestos, áreas or localidades: each person enters those when they activate their account.

```csv
email,company_reference_code,group,auth_method
direccion@empresa.com,A1B2C,Principal Exec,otp
rh@empresa.com,A1B2C,Secondary Exec,otp
ana.lopez@empresa.com,A1B2C,Employees,otp
carlos.ruiz@empresa.com,A1B2C,Employees,password
```

Download the report the import produces and check that every row says `created`. Keep it if any row used `password`: it is the only place the códigos de acceso appear.

The full column rules, the report format and what to do with skipped rows are in [`csv-user-import.md`](csv-user-import.md).

## 3. Assign the survey

Collaborators see nothing to answer until the company has a survey assignment.

1. Go to **Encuestas → Asignaciones de encuesta** and click **Agregar asignación de encuesta**.
2. Fill in:

   | Field | |
   |---|---|
   | **Empresa** | The company from step 1. |
   | **Encuesta** | *Encuesta NOM-035*. |
   | **Variante** | Leave it on **Automática (según número de colaboradores)**. On save it becomes **Guía III** if the company has **more than 50** imported collaborators, **Guía II** otherwise, and a message confirms which one and the count it used. Pick Guía II or Guía III yourself only to override that. Both variants include Guía I (acontecimientos traumáticos severos). |
   | **Estado** | **Activa**. |
   | **Fecha límite** | Optional. The date shown to collaborators as the deadline. |

3. Save.

**Import the users first.** *Automática* counts the collaborators imported into the company at the moment you save, so an assignment created before step 2 always comes out as Guía II.

**Check the variant in the confirmation message.** It is fixed when the assignment is created and decides which questions everyone answers. If it is wrong, delete the assignment and create a new one — but only before anyone has started answering: deleting an assignment also deletes every answer given to it.

Once the assignment exists, each collaborator finds the survey under **Encuestas** (`/encuestas/`) as soon as they have activated their account.

## 4. Hand off to the client

### What to send the company contact

- **The platform address** and the login page, `/cuentas/ingresar/`.
- **The Código de empresa.** Every collaborator types it once, when activating their account. Executives can also copy it from the top of their dashboard (*Copiar*) to pass it on.
- **For `password` users only:** the códigos de acceso from the import report, sent to the company's trusted HR contact through an approved internal channel. HR gives each person their own code. Do not email codes from SOFIA-S to the people whose email is the problem.

The código de empresa is not a password. Share it only with the company itself.

### What each collaborator does on first login

**With a login code by email (`otp`):**

1. Open `/cuentas/ingresar/` and enter their work email.
2. Receive a 6-digit code by email and enter it on the next page (`/cuentas/verificar/`).
3. Complete their profile (below).

**With a código de acceso (`password`):**

1. Open `/cuentas/primer-ingreso/` and enter their work email and the 9-digit código de acceso from HR. The code works once.
2. Create their own password (`/cuentas/cambiar-contrasena/`). From now on they log in at `/cuentas/ingresar-con-contrasena/` with email and password.
3. Complete their profile (below).

**Completing the profile** (`/cuentas/completar-perfil/`), the same for both:

- **Código de empresa** — must match the company their account belongs to.
- **Nombre(s)** and **Apellido paterno** — required. **Apellido materno** — optional.
- **Puesto** — optional.
- **Sexo** and **Fecha de nacimiento** — required. The date is three lists (Día, Mes, Año); the years offered keep the person's age between 15 and 99.
- **Área** — required, from the company's list.
- **Localidad** — only asked when the company has more than one.

After that the account is activated and they go straight in:

| Role | Lands on |
|---|---|
| Ejecutivo principal, Ejecutivo secundario | The company dashboard (`/tablero-empresa/`) |
| Empleado | Their surveys (`/encuestas/`) |

## 5. Follow progress and close the survey

While the survey is open:

- The **roster** (`/tablero-empresa/colaboradores/` for executives; for operators, the company's page under **Empresas**) lists everyone imported. A person who has not activated yet appears by email only, with no name — that is expected, not a failed import.
- The **dashboard** shows how many collaborators have answered.
- Collaborators can leave and come back: their answers are saved as they go.

When the response window ends, go to **Encuestas → Asignaciones de encuesta**, open the assignment, set **Estado** to **Cerrada** and save. Collaborators can no longer answer, and the assignment becomes eligible for the formal results report, which operators draft and publish from the company's page (*Reportes*).

## Troubleshooting

| What happens | Why, and what to do |
|---|---|
| A collaborator is told the company has no áreas | The company has no active área. Add one (step 1); they can then finish activating. |
| "No hay ninguna cuenta con este correo" at login | The email isn't imported, or is typed differently. Check the import report; add them with a new CSV containing only that row. |
| A login code never arrives | Check the platform's email settings ([`platform-setup.md`](platform-setup.md#4-configure-env)). If the company blocks external mail, that person needs the `password` path: delete their user and re-import them with `auth_method` = `password`. |
| "Ese código no corresponde a tu empresa" at activation | The collaborator typed another company's código de empresa, or the CSV linked them to the wrong company. Check their profile under **Cuentas → Perfiles de colaborador**. |
| A código de acceso was exposed before it was used | Delete the user under **Cuentas → Usuarios**, then re-import that one row. The import skips an email that already exists, so deleting first is required; the new import generates a new code. |
| An import row says `skipped` | The report's `message` column says why — usually an unknown código de empresa or group, or an email that already exists. |
| The survey doesn't appear for a collaborator | Check that the company has an assignment with **Estado** *Activa*, and that the collaborator finished activating. |

## Security rules

- Prefer `otp` for everyone whose email works. Never create passwords for them.
- Códigos de acceso go to the company's trusted HR contact through an approved internal channel, never by email from SOFIA-S.
- Treat the import report as sensitive while it holds códigos de acceso. Do not store it in shared folders unless access is restricted.
- Do not use the código de empresa as a password, and share it only with the company it belongs to.
- Give `Admins`, *Es staff* and *Es superusuario* only to platform operators, never to a client user.

## Checklist

- [ ] The company exists, and its **Código de empresa** is copied.
- [ ] The company has at least one active área (and its localidades, if any).
- [ ] Every user is imported, and the import report shows `created` on every row.
- [ ] Each person has the right group: `Principal Exec`, `Secondary Exec` or `Employees`.
- [ ] The company has a survey assignment with the right **Variante**, **Estado** *Activa*, and the agreed **Fecha límite**.
- [ ] The company contact has the platform address and the Código de empresa.
- [ ] HR has the códigos de acceso for every `password` user, through an internal channel.
- [ ] When the window ends, the assignment is set to **Cerrada**.
