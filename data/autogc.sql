BEGIN TRANSACTION;
CREATE TABLE SchemaVersion (
                        version TEXT PRIMARY KEY,
                        applied_on TEXT
                    );
CREATE TABLE canister_types (
                            canister_type TEXT PRIMARY KEY
                        );
INSERT INTO "canister_types" VALUES('CVS');
INSERT INTO "canister_types" VALUES('RTS');
INSERT INTO "canister_types" VALUES('LCS');
CREATE TABLE mdls (
                        site_id INTEGER,
                        aqs_code INTEGER,
                        concentration REAL,
                        units TEXT NOT NULL,
                        date_on TEXT,
                        date_off TEXT,
                        PRIMARY KEY (site_id, aqs_code, date_on),
                        FOREIGN KEY (site_id) REFERENCES sites(site_id)
                    );
INSERT INTO "mdls" VALUES(490353015,43202,0.1751,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43203,0.1108,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43204,0.1818,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43205,0.0731,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43214,0.1571,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43212,0.1362,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43206,0.0682,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43216,0.0433,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43280,0.0592,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43217,0.0396,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43242,0.0339,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43221,0.0614,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43220,0.0292,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43218,0.0544,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43226,0.0524,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43224,0.0454,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43227,0.0349,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43244,0.0393,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43284,0.043,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43285,0.0427,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43230,0.0371,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43243,0.0261,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43245,0.0238,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43231,0.1719,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43262,0.0852,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43247,0.0664,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,45201,0.0531,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43248,0.0844,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43263,0.0785,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43291,0.1252,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43249,0.1086,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43250,0.1032,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43232,0.0733,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43261,0.1688,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43252,0.0923,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,45202,0.1074,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43960,0.0835,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43253,0.0806,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43233,0.0584,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,45203,0.0647,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,45109,0.1121,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,45220,0.0642,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,45204,0.0895,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43235,0.0639,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,45210,0.0546,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43256,0.0901,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,45209,0.0398,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,45212,0.0541,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,45213,0.0756,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,45207,0.0949,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,45211,0.1373,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43257,0.121,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,45208,0.1054,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43238,0.1122,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,45225,0.1355,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,45218,0.0882,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,45219,0.0881,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43954,0.0465,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
INSERT INTO "mdls" VALUES(490353015,43141,0.0972,'ppbc','2024-09-03 00:00:00','2025-05-09 23:59:59');
CREATE TABLE primary_canister_concentration (
                        primary_canister_id TEXT,
                        aqs_code INTEGER,
                        concentration REAL,
                        units TEXT,
                        canister_type TEXT,
                        PRIMARY KEY (primary_canister_id, aqs_code),
                        FOREIGN KEY (primary_canister_id) REFERENCES primary_canisters(primary_canister_id),
                        FOREIGN KEY (aqs_code) REFERENCES voc_info(aqs_code),
                        FOREIGN KEY (canister_type) REFERENCES canister_types(canister_type)
                    );
INSERT INTO "primary_canister_concentration" VALUES('CC524930-0626',43202,0.525,'ppmv','CVS');
INSERT INTO "primary_canister_concentration" VALUES('CC524930-0626',43204,0.34,'ppmv','CVS');
INSERT INTO "primary_canister_concentration" VALUES('CC524930-0626',43212,0.253,'ppmv','CVS');
INSERT INTO "primary_canister_concentration" VALUES('CC524930-0626',43206,0.525,'ppmv','CVS');
INSERT INTO "primary_canister_concentration" VALUES('CC524930-0626',43220,0.204,'ppmv','CVS');
INSERT INTO "primary_canister_concentration" VALUES('CC524930-0626',43218,0.263,'ppmv','CVS');
INSERT INTO "primary_canister_concentration" VALUES('CC524930-0626',43285,0.17,'ppmv','CVS');
INSERT INTO "primary_canister_concentration" VALUES('CC524930-0626',43245,0.17,'ppmv','CVS');
INSERT INTO "primary_canister_concentration" VALUES('CC524930-0626',43231,0.167,'ppmv','CVS');
INSERT INTO "primary_canister_concentration" VALUES('CC524930-0626',45201,0.175,'ppmv','CVS');
INSERT INTO "primary_canister_concentration" VALUES('CC524930-0626',45202,0.146,'ppmv','CVS');
INSERT INTO "primary_canister_concentration" VALUES('CC524930-0626',45109,0.131,'ppmv','CVS');
INSERT INTO "primary_canister_concentration" VALUES('CC524930-0626',45209,0.116,'ppmv','CVS');
INSERT INTO "primary_canister_concentration" VALUES('CC524930-0626',45208,0.113,'ppmv','CVS');
INSERT INTO "primary_canister_concentration" VALUES('CC524930-0626',45219,0.102,'ppmv','CVS');
INSERT INTO "primary_canister_concentration" VALUES('CC177206-0125',43204,0.369,'ppmv','LCS');
INSERT INTO "primary_canister_concentration" VALUES('CC177206-0125',43212,0.279,'ppmv','LCS');
INSERT INTO "primary_canister_concentration" VALUES('CC177206-0125',43202,0.51,'ppmv','LCS');
INSERT INTO "primary_canister_concentration" VALUES('CC177206-0125',43206,0.557,'ppmv','LCS');
INSERT INTO "primary_canister_concentration" VALUES('CC177206-0125',43220,0.228,'ppmv','LCS');
INSERT INTO "primary_canister_concentration" VALUES('CC177206-0125',43218,0.28,'ppmv','LCS');
INSERT INTO "primary_canister_concentration" VALUES('CC177206-0125',43285,0.176,'ppmv','LCS');
INSERT INTO "primary_canister_concentration" VALUES('CC177206-0125',43245,0.18,'ppmv','LCS');
INSERT INTO "primary_canister_concentration" VALUES('CC177206-0125',43231,0.184,'ppmv','LCS');
INSERT INTO "primary_canister_concentration" VALUES('CC177206-0125',45201,0.18,'ppmv','LCS');
INSERT INTO "primary_canister_concentration" VALUES('CC177206-0125',45202,0.142,'ppmv','LCS');
INSERT INTO "primary_canister_concentration" VALUES('CC177206-0125',45109,0.116,'ppmv','LCS');
INSERT INTO "primary_canister_concentration" VALUES('CC177206-0125',45209,0.106,'ppmv','LCS');
INSERT INTO "primary_canister_concentration" VALUES('CC177206-0125',45208,0.103,'ppmv','LCS');
INSERT INTO "primary_canister_concentration" VALUES('CC177206-0125',45219,0.084,'ppmv','LCS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43202,1070.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43203,1070.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43204,1040.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43205,1010.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43214,1060.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43212,1060.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43206,520.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43216,1060.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43280,1060.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43217,1050.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43242,1080.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43221,1100.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43220,1090.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43218,990.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43226,1090.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43224,1130.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43227,1150.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43244,1100.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43284,1070.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43285,1080.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43230,1070.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43243,800.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43245,1060.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43231,1040.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43262,1070.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43247,1070.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',45201,1070.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43248,1060.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43263,1030.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43291,1080.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43249,1070.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43250,1060.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43232,1100.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43261,1060.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43252,1080.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',45202,1080.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43960,1080.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43253,1080.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43233,1200.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',45203,1070.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',45109,1080.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',45220,970.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',45204,1070.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43235,1090.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',45210,1070.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',45209,1040.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',45212,1080.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',45213,1010.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',45207,1070.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',45211,1050.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',45208,1040.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43238,1070.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',45225,1020.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',45218,1020.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',45219,1030.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43954,1030.0,'ppbc','RTS');
INSERT INTO "primary_canister_concentration" VALUES('CC731198-0126',43141,980.0,'ppbc','RTS');
CREATE TABLE primary_canisters (
                        primary_canister_id TEXT PRIMARY KEY,
                        canister_type TEXT NOT NULL,
                        expiration_date TEXT,
                        FOREIGN KEY(canister_type) REFERENCES canister_types(canister_type)
                    );
INSERT INTO "primary_canisters" VALUES('CC524930-0626','CVS','2026-06-01 00:00:00');
INSERT INTO "primary_canisters" VALUES('CC177206-0125','LCS','2025-01-01 00:00:00');
INSERT INTO "primary_canisters" VALUES('CC731198-0126','RTS','2026-01-01 00:00:00');
CREATE TABLE site_canisters (
                        site_canister_id TEXT PRIMARY KEY,
                        site_id INTEGER NOT NULL,
                        primary_canister_id TEXT NOT NULL,
                        dilution_ratio REAL,
                        date_on TEXT,
                        date_off TEXT,
                        FOREIGN KEY (site_id) REFERENCES sites(site_id),
                        FOREIGN KEY (primary_canister_id) REFERENCES primary_canisters(primary_canister_id)
                    );
INSERT INTO "site_canisters" VALUES('3667',490353015,'CC524930-0626',0.00189,'2024-09-07 00:00:00','2025-04-16 08:59:59');
INSERT INTO "site_canisters" VALUES('3692',490353015,'CC177206-0125',0.005,'2024-09-13 00:00:00','2024-11-06 09:59:59');
INSERT INTO "site_canisters" VALUES('3733',490353015,'CC177206-0125',0.005,'2024-11-06 10:00:00','2025-04-15 23:59:59');
INSERT INTO "site_canisters" VALUES('49054',490353015,'CC731198-0126',0.0013,'2024-03-08 00:00:00',NULL);
CREATE TABLE sites (
                        site_id INTEGER PRIMARY KEY,
                        name_short TEXT UNIQUE,
                        name_long TEXT UNIQUE,
                        lat REAL,
                        long REAL,
                        date_started TEXT
                    );
INSERT INTO "sites" VALUES(490353015,'EQ','Utah Technical Center',40.7770994964404,-1.119450044213330954e+02,'2023-10-01 00:00:00');
CREATE TABLE voc_info (
                        aqs_code INTEGER PRIMARY KEY,
                        compound TEXT,
                        category TEXT,
                        carbon_count INTEGER,
                        molecular_weight REAL,
                        column TEXT,
                        elution_order INTEGER,
                        priority BOOLEAN
                    );
INSERT INTO "voc_info" VALUES(43141,'N-dodecane','Alkane',12,170.34,'BP',36,0);
INSERT INTO "voc_info" VALUES(43202,'Ethane','Alkane',2,30.07,'PLOT',1,1);
INSERT INTO "voc_info" VALUES(43203,'Ethylene','Alkene',2,28.05,'PLOT',2,1);
INSERT INTO "voc_info" VALUES(43204,'Propane','Alkane',3,44.097,'PLOT',3,1);
INSERT INTO "voc_info" VALUES(43205,'Propylene','Alkene',3,42.081,'PLOT',4,1);
INSERT INTO "voc_info" VALUES(43206,'Acetylene','Alkyne',2,26.038,'PLOT',7,0);
INSERT INTO "voc_info" VALUES(43212,'N-butane','Alkane',4,58.12,'PLOT',6,1);
INSERT INTO "voc_info" VALUES(43214,'Iso-butane','Alkane',4,58.12,'PLOT',5,1);
INSERT INTO "voc_info" VALUES(43216,'Trans-2-butene','Alkene',4,56.11,'PLOT',8,1);
INSERT INTO "voc_info" VALUES(43217,'Cis-2-butene','Alkene',4,56.11,'PLOT',10,1);
INSERT INTO "voc_info" VALUES(43218,'1,3-butadiene','Alkene',4,54.0916,'PLOT',14,0);
INSERT INTO "voc_info" VALUES(43220,'N-pentane','Alkane',5,72.15,'PLOT',13,1);
INSERT INTO "voc_info" VALUES(43221,'Iso-pentane','Alkane',5,72.15,'PLOT',12,1);
INSERT INTO "voc_info" VALUES(43224,'1-pentene','Alkene',5,70.134,'PLOT',16,0);
INSERT INTO "voc_info" VALUES(43226,'Trans-2-pentene','Alkene',5,70.13,'PLOT',15,0);
INSERT INTO "voc_info" VALUES(43227,'Cis-2-pentene','Alkene',5,70.134,'PLOT',17,0);
INSERT INTO "voc_info" VALUES(43230,'3-methylpentane','Alkane',6,86.18,'PLOT',21,0);
INSERT INTO "voc_info" VALUES(43231,'N-hexane','Alkane',6,86.17848,'BP',1,1);
INSERT INTO "voc_info" VALUES(43232,'N-heptane','Alkane',7,100.21,'BP',10,0);
INSERT INTO "voc_info" VALUES(43233,'N-octane','Alkane',8,114.23,'BP',16,0);
INSERT INTO "voc_info" VALUES(43235,'N-nonane','Alkane',9,128.2,'BP',21,0);
INSERT INTO "voc_info" VALUES(43238,'N-decane','Alkane',10,142.28,'BP',31,0);
INSERT INTO "voc_info" VALUES(43242,'Cyclopentane','Alkane',5,70.13,'PLOT',11,0);
INSERT INTO "voc_info" VALUES(43243,'Isoprene','Terpene',5,68.12,'PLOT',22,1);
INSERT INTO "voc_info" VALUES(43244,'2,2-dimethylbutane','Alkane',6,86.17,'PLOT',18,0);
INSERT INTO "voc_info" VALUES(43245,'1-hexene','Alkene',6,84.1608,'PLOT',24,0);
INSERT INTO "voc_info" VALUES(43246,'2-methyl-1-pentene','Alkene',6,84.16,'PLOT',23,0);
INSERT INTO "voc_info" VALUES(43247,'2,4-dimethylpentane','Alkane',7,100.2,'BP',3,0);
INSERT INTO "voc_info" VALUES(43248,'Cyclohexane','Alkane',6,84.16,'BP',5,0);
INSERT INTO "voc_info" VALUES(43249,'3-methylhexane','Alkane',7,100.2,'BP',8,0);
INSERT INTO "voc_info" VALUES(43250,'2,2,4-trimethylpentane','Alkane',8,114.23,'BP',9,1);
INSERT INTO "voc_info" VALUES(43252,'2,3,4-trimethylpentane','Alkane',8,114.23,'BP',12,0);
INSERT INTO "voc_info" VALUES(43253,'3-methylheptane','Alkane',8,114.23,'BP',15,0);
INSERT INTO "voc_info" VALUES(43256,'Alpha-pinene','Terpene',10,136.23,'BP',23,0);
INSERT INTO "voc_info" VALUES(43257,'Beta-pinene','Terpene',10,136.23,'BP',29,0);
INSERT INTO "voc_info" VALUES(43261,'Methylcyclohexane','Alkane',7,98.186,'BP',11,0);
INSERT INTO "voc_info" VALUES(43262,'Methylcyclopentane','Alkane',6,84.16,'BP',2,0);
INSERT INTO "voc_info" VALUES(43263,'2-methylhexane','Alkane',7,100.2,'BP',6,0);
INSERT INTO "voc_info" VALUES(43280,'1-butene','Alkene',4,56.11,'PLOT',9,1);
INSERT INTO "voc_info" VALUES(43284,'2,3-dimethylbutane','Alkane',6,86.17,'PLOT',19,0);
INSERT INTO "voc_info" VALUES(43285,'2-methylpentane','Alkane',6,86.18,'PLOT',20,0);
INSERT INTO "voc_info" VALUES(43291,'2,3-dimethylpentane','Alkane',7,100.2,'BP',7,0);
INSERT INTO "voc_info" VALUES(43954,'N-undecane','Alkane',11,156.31,'BP',35,0);
INSERT INTO "voc_info" VALUES(43960,'2-methylheptane','Alkane',8,114.23,'BP',14,0);
INSERT INTO "voc_info" VALUES(45109,'M&p-xylene','Aromatic',8,106.16,'BP',18,1);
INSERT INTO "voc_info" VALUES(45201,'Benzene','Aromatic',6,78.11,'BP',4,1);
INSERT INTO "voc_info" VALUES(45202,'Toluene','Aromatic',7,92.14,'BP',13,1);
INSERT INTO "voc_info" VALUES(45203,'Ethylbenzene','Aromatic',8,106.167,'BP',17,1);
INSERT INTO "voc_info" VALUES(45204,'O-xylene','Aromatic',8,106.16,'BP',20,1);
INSERT INTO "voc_info" VALUES(45207,'1,3,5-tri-m-benzene','Aromatic',9,120.19,'BP',27,0);
INSERT INTO "voc_info" VALUES(45208,'1,2,4-tri-m-benzene','Aromatic',9,120.19,'BP',30,1);
INSERT INTO "voc_info" VALUES(45209,'N-propylbenzene','Aromatic',9,120.2,'BP',24,0);
INSERT INTO "voc_info" VALUES(45210,'Iso-propylbenzene','Aromatic',9,120.19,'BP',22,0);
INSERT INTO "voc_info" VALUES(45211,'O-ethyltoluene','Aromatic',9,120.19,'BP',28,1);
INSERT INTO "voc_info" VALUES(45212,'M-ethyltoluene','Aromatic',9,120.19,'BP',25,1);
INSERT INTO "voc_info" VALUES(45213,'P-ethyltoluene','Aromatic',9,120.19,'BP',26,1);
INSERT INTO "voc_info" VALUES(45218,'M-diethylbenzene','Aromatic',10,134.22,'BP',33,0);
INSERT INTO "voc_info" VALUES(45219,'P-diethylbenzene','Aromatic',10,134.22,'BP',34,0);
INSERT INTO "voc_info" VALUES(45220,'Styrene','Aromatic',8,104.15,'BP',19,1);
INSERT INTO "voc_info" VALUES(45225,'1,2,3-tri-m-benzene','Aromatic',9,120.19,'BP',32,1);
COMMIT;