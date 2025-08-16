# Dynamic REST IoT Platform

This project provides a containerized IoT interface platform with:
- **Nginx Webserver** serving the frontend interface
- **FastAPI Interface Service** for backend logic
- **PostgreSQL Database** for persistent storage

## 📂 Project Structure

```
project-root/
│
├── nginx/                  # Nginx Docker build context
│   ├── Dockerfile
│   └── config/             # Custom Nginx configuration files
│   └── web/                # Main website html
│
├── interface/              # Backend FastAPI service
│   └── ... (Python source files)
│
├── utilities/              # SQL and helper scripts
│   ├── dbconstruct.sql
│
├── docker-compose.yml
└── README.md
```

---

## 🚀 Services

### 1. **webserver**
- **Base Image**: `nginx:latest`
- Serves frontend files from `../web/main/`
- Uses custom config from `../backend/nginx/config/`
- Ports:
  - `80` → HTTP
  - `443` → HTTPS

### 2. **interface**
- **Base**: Python / FastAPI
- Environment variables:
  - `DB_USER`
  - `DB_PASS`
  - `DB_NAME`
  - `DB_HOST`
- Port: `8888`

### 3. **database**
- **Image**: `postgres:14.5`
- Environment variables:
  - `POSTGRES_USER`
  - `POSTGRES_PASSWORD`
  - `POSTGRES_DB`
- Port: `5432`
- Auto-initializes with `utilities/dbconstruct.sql`

---

## ⚙️ Prerequisites

- Docker (20+ recommended)
- Docker Compose (v2+ recommended)
- Git
- Optional: Makefile for automation

---

## 📦 Setup & Run

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/dynamic-rest-iot.git
   cd dynamic-rest-iot
   ```

2. **Set environment variables**
   Create a `.env` file in the root directory:
   ```env
   DB_USER=postgres
   DB_PASS=yourpassword
   DB_NAME=yourdbname
   DB_HOST=database
   ```

3. **Build and start the containers**
   ```bash
   docker compose up --build
   ```

4. **Access the application**
   - Web Interface: http://localhost
   - Backend API: http://localhost:8888
   - Database: localhost:5432

---

## 🔧 Development Notes

- **Frontend files** are served from the `web/main/` directory.  
  
- **Custom Nginx Config**: Place `.conf` files inside `nginx/config/` and they will override defaults.

- **Database Init**: Any `.sql` files in `utilities/` can be mounted into `/docker-entrypoint-initdb.d/` to auto-run when the database container is first created.

---

## 🛠 Troubleshooting

- **403 Forbidden**: Ensure `index.html` exists in `web/main/`.
- **Nginx Config Missing Warning**: If you override `/etc/nginx/conf.d/`, ensure it contains at least one valid `.conf` file.
- **Database Connection Errors**: Confirm `.env` values match between `interface` service and `database` service.

---

## 📜 License
All rights reserved.

- The Software may **not** be used, copied, modified, merged, published, distributed, sublicensed, or sold for **commercial purposes**, in whole or in part, without prior written permission from the copyright holder.
- The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE APPLICATION IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
